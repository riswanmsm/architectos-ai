import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import BaseModel

from architectos_llm.providers import (
    AnthropicProvider,
    OpenAICompatibleProvider,
    ProviderError,
    _without_schema_keywords,
    create_provider,
    load_provider_registry,
    resolve_provider_settings,
)


class ExampleOutput(BaseModel):
    value: str


class ProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_provider_registry(Path("config/providers.json"))

    def test_registry_contains_supported_providers(self) -> None:
        self.assertEqual(
            {"gemini", "openai", "deepseek", "anthropic"},
            set(self.registry),
        )

    def test_environment_selects_provider_and_model(self) -> None:
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "deepseek", "LLM_MODEL": "deepseek-v4-pro"},
            clear=False,
        ):
            settings = resolve_provider_settings(self.registry, None, None)
        self.assertEqual("deepseek", settings.provider_name)
        self.assertEqual("deepseek-v4-pro", settings.model)
        self.assertEqual(0.435, settings.pricing.input_price_per_million)

    def test_unknown_model_is_allowed_without_assumed_pricing(self) -> None:
        settings = resolve_provider_settings(
            self.registry,
            "gemini",
            "gemini-future-model",
        )
        self.assertEqual("gemini-future-model", settings.model)
        self.assertIsNone(settings.pricing.input_price_per_million)

    def test_missing_provider_key_has_clear_error(self) -> None:
        settings = resolve_provider_settings(self.registry, "deepseek", None)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ProviderError, "DEEPSEEK_API_KEY"):
                create_provider(settings)

    @patch("architectos_llm.providers._post_json")
    def test_openai_adapter_uses_strict_json_schema(self, post_json) -> None:
        post_json.return_value = {
            "id": "request-1",
            "choices": [{"message": {"content": '{"value":"ok"}'}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 4},
        }
        provider = OpenAICompatibleProvider(
            "secret",
            "gpt-test",
            "https://example.test/v1",
            "json_schema",
            "max_completion_tokens",
            100,
            10,
        )
        result = provider.generate_structured("return JSON", ExampleOutput)
        body = post_json.call_args.args[2]
        self.assertEqual("json_schema", body["response_format"]["type"])
        self.assertTrue(body["response_format"]["json_schema"]["strict"])
        self.assertEqual(100, body["max_completion_tokens"])
        self.assertEqual(12, result.input_tokens)

    @patch("architectos_llm.providers._post_json")
    def test_deepseek_style_adapter_uses_json_object(self, post_json) -> None:
        post_json.return_value = {
            "id": "request-2",
            "choices": [{"message": {"content": '{"value":"ok"}'}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 3},
        }
        provider = OpenAICompatibleProvider(
            "secret",
            "deepseek-test",
            "https://example.test",
            "json_object",
            "max_tokens",
            100,
            10,
        )
        provider.generate_structured("return JSON", ExampleOutput)
        body = post_json.call_args.args[2]
        self.assertEqual({"type": "json_object"}, body["response_format"])
        self.assertEqual(100, body["max_tokens"])

    @patch("architectos_llm.providers._post_json")
    def test_anthropic_adapter_uses_output_schema(self, post_json) -> None:
        post_json.return_value = {
            "id": "request-3",
            "content": [{"type": "text", "text": '{"value":"ok"}'}],
            "usage": {"input_tokens": 9, "output_tokens": 3},
        }
        provider = AnthropicProvider(
            "secret",
            "claude-test",
            "https://example.test",
            "2023-06-01",
            100,
            10,
        )
        result = provider.generate_structured("return JSON", ExampleOutput)
        body = post_json.call_args.args[2]
        self.assertEqual("json_schema", body["output_config"]["format"]["type"])
        self.assertEqual("request-3", result.request_id)

    def test_registry_is_valid_json(self) -> None:
        raw = json.loads(Path("config/providers.json").read_text(encoding="utf-8"))
        self.assertEqual("gemini", raw["gemini"]["adapter"])

    def test_provider_schema_filter_is_recursive(self) -> None:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "child": {
                    "type": "object",
                    "additionalProperties": False,
                }
            },
        }
        filtered = _without_schema_keywords(schema, {"additionalProperties"})
        self.assertNotIn("additionalProperties", filtered)
        self.assertNotIn("additionalProperties", filtered["properties"]["child"])


if __name__ == "__main__":
    unittest.main()
