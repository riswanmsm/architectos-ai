import json
import os
import re
from dataclasses import dataclass

from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field


class ProviderError(RuntimeError):
    """A sanitized provider configuration or generation failure."""


class ModelPricing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_price_per_million: float | None = Field(default=None, ge=0)
    output_price_per_million: float | None = Field(default=None, ge=0)


class ProviderDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adapter: Literal["gemini", "openai_compatible", "anthropic"]
    key_env: str
    default_model: str
    base_url: str | None = None
    response_mode: Literal["json_schema", "json_object"] = "json_schema"
    max_tokens_field: Literal["max_tokens", "max_completion_tokens"] = "max_tokens"
    api_version: str | None = None
    max_output_tokens: int = Field(default=16000, gt=0)
    timeout_seconds: int = Field(default=120, gt=0)
    models: dict[str, ModelPricing] = Field(default_factory=dict)


@dataclass(frozen=True)
class ProviderSettings:
    provider_name: str
    model: str
    definition: ProviderDefinition
    pricing: ModelPricing


@dataclass(frozen=True)
class ProviderResult:
    raw_text: str
    input_tokens: int | None
    output_tokens: int | None
    request_id: str | None


class StructuredProvider(Protocol):
    def generate_text(self, prompt: str) -> ProviderResult:
        ...

    def generate_structured(self, prompt: str, schema: type[BaseModel]) -> ProviderResult:
        ...


def load_provider_registry(path: Path) -> dict[str, ProviderDefinition]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not raw:
        raise ProviderError("Provider registry must contain at least one provider.")
    return {
        name: ProviderDefinition.model_validate(definition)
        for name, definition in raw.items()
    }


def resolve_provider_settings(
    registry: dict[str, ProviderDefinition],
    provider_name: str | None,
    model: str | None,
) -> ProviderSettings:
    selected_provider = provider_name or os.getenv("LLM_PROVIDER", "gemini")
    if selected_provider not in registry:
        available = ", ".join(sorted(registry))
        raise ProviderError(
            f"Unknown provider '{selected_provider}'. Available providers: {available}."
        )
    definition = registry[selected_provider]
    selected_model = model or os.getenv("LLM_MODEL") or definition.default_model
    pricing = definition.models.get(selected_model, ModelPricing())
    return ProviderSettings(selected_provider, selected_model, definition, pricing)


def _redact(text: str, secret: str) -> str:
    return text.replace(secret, "[REDACTED]") if secret else text


def _without_schema_keywords(value: Any, unsupported: set[str]) -> Any:
    """Remove provider-unsupported JSON Schema keywords without changing local validation."""
    if isinstance(value, dict):
        return {
            key: _without_schema_keywords(item, unsupported)
            for key, item in value.items()
            if key not in unsupported
        }
    if isinstance(value, list):
        return [_without_schema_keywords(item, unsupported) for item in value]
    return value


def _post_json(
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    timeout_seconds: int,
    secret: str,
) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(
            _redact(f"Provider returned HTTP {exc.code}: {detail}", secret)
        ) from exc
    except URLError as exc:
        raise ProviderError(_redact(f"Provider request failed: {exc.reason}", secret)) from exc
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ProviderError("Provider returned a non-JSON HTTP response.") from exc
    if not isinstance(parsed, dict):
        raise ProviderError("Provider returned an unexpected HTTP response shape.")
    return parsed


class GeminiProvider:
    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._api_key = api_key
        self._model = model

    def generate_text(self, prompt: str) -> ProviderResult:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
        except Exception as exc:
            raise ProviderError(_redact(str(exc), self._api_key)) from exc
        return self._result(response)

    def generate_structured(self, prompt: str, schema: type[BaseModel]) -> ProviderResult:
        from google.genai import types

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_without_schema_keywords(
                        schema.model_json_schema(),
                        {"additionalProperties"},
                    ),
                ),
            )
        except Exception as exc:
            raise ProviderError(_redact(str(exc), self._api_key)) from exc
        return self._result(response)

    @staticmethod
    def _result(response: Any) -> ProviderResult:
        usage = response.usage_metadata
        return ProviderResult(
            raw_text=response.text or "",
            input_tokens=getattr(usage, "prompt_token_count", None) if usage else None,
            output_tokens=getattr(usage, "candidates_token_count", None) if usage else None,
            request_id=getattr(response, "response_id", None),
        )


class OpenAICompatibleProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        response_mode: str,
        max_tokens_field: str,
        max_output_tokens: int,
        timeout_seconds: int,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._response_mode = response_mode
        self._max_tokens_field = max_tokens_field
        self._max_output_tokens = max_output_tokens
        self._timeout_seconds = timeout_seconds

    def _generate(
        self,
        prompt: str,
        response_format: dict[str, Any] | None,
    ) -> ProviderResult:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            self._max_tokens_field: self._max_output_tokens,
            "stream": False,
        }
        if response_format is not None:
            body["response_format"] = response_format
        payload = _post_json(
            f"{self._base_url}/chat/completions",
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            body,
            self._timeout_seconds,
            self._api_key,
        )
        try:
            raw_text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("OpenAI-compatible provider returned no message content.") from exc
        if not isinstance(raw_text, str) or not raw_text.strip():
            raise ProviderError("OpenAI-compatible provider returned empty message content.")
        
        # Strip potential markdown fences from raw output
        raw_text = re.sub(r"^```(?:json)?\s*\n?", "", raw_text.strip())
        raw_text = re.sub(r"\n?```\s*$", "", raw_text).strip()

        usage = payload.get("usage") or {}
        return ProviderResult(
            raw_text=raw_text,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            request_id=payload.get("id"),
        )

    def generate_text(self, prompt: str) -> ProviderResult:
        return self._generate(prompt, None)

    def generate_structured(self, prompt: str, schema: type[BaseModel]) -> ProviderResult:
        if self._response_mode == "json_schema":
            response_format: dict[str, Any] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "architectos_blueprint",
                    "strict": True,
                    "schema": _without_schema_keywords(
                        schema.model_json_schema(),
                        {"additionalProperties"},
                    ),
                },
            }
        else:
            response_format = {"type": "json_object"}
        return self._generate(prompt, response_format)



class AnthropicProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        api_version: str,
        max_output_tokens: int,
        timeout_seconds: int,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._api_version = api_version
        self._max_output_tokens = max_output_tokens
        self._timeout_seconds = timeout_seconds

    def _generate(
        self,
        prompt: str,
        output_config: dict[str, Any] | None,
    ) -> ProviderResult:
        body: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_output_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if output_config is not None:
            body["output_config"] = output_config
        payload = _post_json(
            f"{self._base_url}/v1/messages",
            {
                "x-api-key": self._api_key,
                "anthropic-version": self._api_version,
                "Content-Type": "application/json",
            },
            body,
            self._timeout_seconds,
            self._api_key,
        )
        content = payload.get("content") or []
        raw_text = next(
            (item.get("text") for item in content if item.get("type") == "text"),
            None,
        )
        if not isinstance(raw_text, str) or not raw_text.strip():
            raise ProviderError("Anthropic provider returned empty message content.")
        usage = payload.get("usage") or {}
        return ProviderResult(
            raw_text=raw_text,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            request_id=payload.get("id"),
        )

    def generate_text(self, prompt: str) -> ProviderResult:
        return self._generate(prompt, None)

    def generate_structured(self, prompt: str, schema: type[BaseModel]) -> ProviderResult:
        return self._generate(
            prompt,
            {
                "format": {
                    "type": "json_schema",
                    "schema": schema.model_json_schema(),
                }
            },
        )


def create_provider(settings: ProviderSettings) -> StructuredProvider:
    definition = settings.definition
    api_key = os.getenv(definition.key_env)
    if not api_key:
        if settings.provider_name == "ollama" or (definition.base_url and "11434" in definition.base_url):
            api_key = "ollama"
        else:
            raise ProviderError(
                f"{definition.key_env} is required for provider '{settings.provider_name}'."
            )

    if definition.adapter == "gemini":
        return GeminiProvider(api_key, settings.model)
    if not definition.base_url:
        raise ProviderError(
            f"Provider '{settings.provider_name}' requires a base_url."
        )
    if definition.adapter == "openai_compatible":
        return OpenAICompatibleProvider(
            api_key,
            settings.model,
            definition.base_url,
            definition.response_mode,
            definition.max_tokens_field,
            definition.max_output_tokens,
            definition.timeout_seconds,
        )
    if definition.adapter == "anthropic":
        if not definition.api_version:
            raise ProviderError("Anthropic provider requires api_version.")
        return AnthropicProvider(
            api_key,
            settings.model,
            definition.base_url,
            definition.api_version,
            definition.max_output_tokens,
            definition.timeout_seconds,
        )
    raise ProviderError(f"Unsupported adapter '{definition.adapter}'.")
