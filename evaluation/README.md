# ArchitectOS Evaluation

## Purpose

This directory defines the frozen comparison between a one-prompt baseline and the final ArchitectOS agent workflow.

## Version

Evaluation specification: `v1.0.0`

Changing a case or scoring rule after inspecting results requires a new version. Previous results must remain available and must not be silently overwritten.

## Inputs

- `cases.json`: ten synthetic application ideas and case-specific obligations
- `rubric.md`: scoring rules applied to both systems

## Baseline Commands

Run the offline validation suite from the repository root:

```bash
backend/.venv/bin/python -m unittest discover -s evaluation/tests -v
```

Run one case before spending resources on the complete baseline:

```bash
backend/.venv/bin/python -m evaluation.baseline --case CASE-01
```

Run all ten frozen cases:

```bash
backend/.venv/bin/python -m evaluation.baseline
```

The runner reads `LLM_PROVIDER`, `LLM_MODEL`, and the selected provider key from the process environment or ignored root `.env` file. It never writes keys to evidence files. Existing case results are not overwritten unless `--overwrite` is supplied.

Override the configured provider or model explicitly:

```bash
backend/.venv/bin/python -m evaluation.baseline \
  --provider deepseek \
  --model deepseek-v4-flash \
  --case CASE-01
```

Provider definitions live in `config/providers.json`; extension instructions are in `docs/model-providers.md`.

To calculate approximate cost, supply prices explicitly so historical results do not silently change when provider pricing changes:

```bash
backend/.venv/bin/python -m evaluation.baseline \
  --input-price-per-million INPUT_PRICE \
  --output-price-per-million OUTPUT_PRICE
```

Every case records its prompt, raw response, validated blueprint, verifier report, provider/model identity, runtime metadata, and failure information under `evaluation/results/baseline/<provider>-<model>/`. A top-level `summary.json` includes all cases, including failures.

Recompute scores from preserved blueprints without making model calls:

```bash
backend/.venv/bin/python -m evaluation.rescore \
  evaluation/results/baseline/<provider>-<model>
```

Scorer implementation corrections are recorded in `evaluation/CHANGELOG.md`; cases, prompts, and raw model outputs are not altered by rescoring.

Commands for the final agent solution and comparison report will be added in their implementation phases.

## Evidence Policy

- Preserve raw model outputs.
- Preserve invalid outputs and runtime failures.
- Record model name, prompt version, timestamps, latency, token usage when available, and approximate cost.
- Do not include API keys, private information, or proprietary datasets.
- Use only the synthetic cases committed here for the primary comparison.
