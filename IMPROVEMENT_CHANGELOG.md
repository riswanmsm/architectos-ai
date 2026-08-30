# Improvement Changelog

This changelog records competition experiments performed after pre-event commit `714b994`. Evidence links must point to committed evaluation outputs. Planned work is not presented as a measured result.

| Stage | What we tried and why | Evidence | Decision / learning | Status |
|---|---|---|---|---|
| Pre-event system | Eight specialist personas generated blueprint sections in sequence, with a fixed risk rejection and retry for demonstration. | Repository at `714b994` | Established the existing product and exposed that displayed confidence and readiness were not evidence-derived. | Complete |
| Provider abstraction | Normalized Gemini, OpenAI-compatible, DeepSeek, and Anthropic calls so provider choice is configuration rather than orchestration logic. | 18 offline tests; successful Gemini 3.7 Flash `CASE-01` smoke result under `evaluation/results/baseline/gemini-gemini-3.7-flash/` | Kept. The adapter isolated a Gemini schema incompatibility while local Pydantic validation remained unchanged. | Complete |
| Baseline | Use one direct prompt with the same idea and output schema to measure a reasonable basic approach. The runner, scorer, and one-case smoke test are complete; the frozen ten-case run is pending. | Smoke only: `evaluation/results/baseline/gemini-gemini-3.7-flash/` | `CASE-01` reached 100 VBC after correcting evaluator handling of valid NFR references. Run all cases before drawing a conclusion. | In progress |
| Iteration 1 | Add shared structured context so downstream specialists consume upstream artifacts. | Pending | Pending | Planned |
| Iteration 2 | Add deterministic verification after observing cross-artifact inconsistencies. | Pending | Pending | Planned |
| Iteration 3 | Add targeted repair so verifier evidence reopens only the responsible artifact. | Pending | Pending | Planned |
| Removed experiment | Record at least one tested idea that was removed, why it failed, and what it taught us. This entry must not be invented in advance. | Pending | Pending | Required before submission |
| Final | Combine only changes supported by the frozen evaluation. | Pending: `evaluation/results/final/` | Identify the largest measured contribution and principal failure mode. | Planned |

## Entry Requirements

For every implemented experiment, record:

- Hypothesis
- Exact code or prompt change
- Evaluation version and cases used
- Complete metric results
- Runtime and approximate cost
- Failures or regressions
- Keep, revise, or remove decision

## Main Failure Mode and Hot Take

To be completed from observed evaluation evidence. The current hypothesis is that fluent specialist documents can appear collaborative while hiding broken cross-artifact dependencies. This must be confirmed or rejected by the evaluation rather than stated as a result now.
