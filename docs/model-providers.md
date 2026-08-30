# Model Provider Configuration

ArchitectOS uses the provider-neutral interface in `architectos_llm/providers.py`. Both the live backend and evaluation runner select providers through `config/providers.json` and environment variables.

## Select a configured provider

Keep secrets only in the ignored root `.env` file:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.7-flash
GEMINI_API_KEY=replace_with_your_key
```

Configured alternatives are `openai`, `deepseek`, and `anthropic`. Set the matching key variable shown in `.env.example`.

## Add a model from an existing provider

If pricing metadata is not required, change only `LLM_MODEL`. ArchitectOS accepts model IDs that are not listed in the registry and records cost as unknown.

To calculate cost automatically, add the model to the provider's `models` object:

```json
"new-model-id": {
  "input_price_per_million": 0.0,
  "output_price_per_million": 0.0
}
```

Pricing is evidence metadata, not a request parameter. Verify current official pricing before editing it.

## Add an OpenAI-compatible provider

Add a registry entry without changing Python code:

```json
"new_provider": {
  "adapter": "openai_compatible",
  "key_env": "NEW_PROVIDER_API_KEY",
  "base_url": "https://provider.example/v1",
  "default_model": "provider-model-id",
  "response_mode": "json_schema",
  "max_tokens_field": "max_tokens",
  "models": {}
}
```

Use `response_mode: "json_object"` when the provider guarantees JSON but does not implement strict JSON Schema. All returned data is still validated with the shared Pydantic blueprint schema.

Add the key variable to `.env`:

```env
LLM_PROVIDER=new_provider
LLM_MODEL=provider-model-id
NEW_PROVIDER_API_KEY=replace_with_your_key
```

Do not add the real key to `.env.example`, `providers.json`, screenshots, trajectories, or evaluation evidence.

## Add a provider with a new protocol

Implement `generate_text` and `generate_structured` using the `StructuredProvider` protocol, add the adapter name to `ProviderDefinition`, and route it in `create_provider`. Provider results must normalize raw text, input tokens, output tokens, and request ID.

## Reproducible evaluation

Provider portability and evaluation fairness are separate concerns. Record the exact provider and model for every run. Compare the baseline and final workflow using the same provider and model.
