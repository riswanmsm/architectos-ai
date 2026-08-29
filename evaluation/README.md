# ArchitectOS Evaluation

## Purpose

This directory defines the frozen comparison between a one-prompt baseline and the final ArchitectOS agent workflow.

## Version

Evaluation specification: `v1.0.0`

Changing a case or scoring rule after inspecting results requires a new version. Previous results must remain available and must not be silently overwritten.

## Inputs

- `cases.json`: ten synthetic application ideas and case-specific obligations
- `rubric.md`: scoring rules applied to both systems

## Planned Commands

Exact executable commands will be added with the baseline and evaluation runner. The final interface will provide separate commands for:

```text
run baseline
run agent solution
score both result sets
produce comparison report
```

## Evidence Policy

- Preserve raw model outputs.
- Preserve invalid outputs and runtime failures.
- Record model name, prompt version, timestamps, latency, token usage when available, and approximate cost.
- Do not include API keys, private information, or proprietary datasets.
- Use only the synthetic cases committed here for the primary comparison.
