import os
from pathlib import Path

from architectos_llm import (
    ProviderError,
    StructuredProvider,
    create_provider,
    load_provider_registry,
    resolve_provider_settings,
)


_provider: StructuredProvider | None = None
_initialization_attempted = False


def _candidate_paths(relative_path: str) -> list[Path]:
    source = Path(__file__).resolve()
    candidates = [
        Path.cwd() / relative_path,
        Path.cwd().parent / relative_path,
        source.parents[2] / relative_path,
        source.parents[3] / relative_path,
    ]
    return list(dict.fromkeys(candidates))


def _load_local_env() -> None:
    for path in _candidate_paths(".env"):
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return


def _find_registry() -> Path:
    configured = os.getenv("LLM_PROVIDER_CONFIG")
    if configured:
        path = Path(configured)
        if path.exists():
            return path
        raise ProviderError(f"LLM provider registry not found: {path}")
    for path in _candidate_paths("config/providers.json"):
        if path.exists():
            return path
    raise ProviderError("Could not locate config/providers.json.")


def _get_provider() -> StructuredProvider | None:
    global _provider, _initialization_attempted
    if _initialization_attempted:
        return _provider
    _initialization_attempted = True
    try:
        _load_local_env()
        registry = load_provider_registry(_find_registry())
        settings = resolve_provider_settings(registry, None, None)
        _provider = create_provider(settings)
        print(f"ArchitectOS LLM provider initialized: {settings.provider_name}/{settings.model}")
    except Exception as exc:
        print(f"Warning: LLM provider unavailable ({exc}). Using fallback templates.")
        _provider = None
    return _provider


def generate_with_llm(prompt: str, fallback_content: str) -> str:
    """Generate text through the configured provider and safely fall back offline."""
    provider = _get_provider()
    if provider is None:
        return fallback_content
    try:
        response = provider.generate_text(prompt)
        return response.raw_text.strip() or fallback_content
    except Exception as exc:
        print(f"LLM generation failed ({exc}). Using fallback template.")
        return fallback_content
