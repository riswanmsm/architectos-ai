# ArchitectOS Hackathon Submission Plan

## Competition Boundary

The project state through commit `714b994` existed before the official competition start.

### Pre-existing system

- React and FastAPI application shell
- Eight engineering specialist personas and Markdown skill contracts
- Sequential browser-driven workflow
- Gemini text generation with offline fallback templates
- Demonstration-only architecture rejection and retry sequence
- Docker-based local launch and existing demo assets

The pre-existing retry sequence uses fixed risk outcomes and does not verify generated artifacts. Session history is initialized but is not yet used to pass specialist outputs downstream.

### Competition work

Competition work begins after commit `714b994`. Planned additions are:

- A reproducible one-prompt baseline
- A fixed synthetic evaluation set and scoring rubric
- Shared structured context between specialists
- A Blueprint Proof Graph linking requirements to implementation and tests
- Deterministic verification and evidence-derived readiness scoring
- Targeted repair driven by verifier findings
- Agent trajectory capture
- Reproducible evaluation and submission evidence

All additions and experiments will be recorded in `IMPROVEMENT_CHANGELOG.md`. Results will only be reported after they are produced by the committed evaluation workflow.

## Intended User

### Primary user

Founders and non-technical product creators who have a software application idea but do not yet have a complete, internally consistent engineering specification.

### Broader audience

Anyone with a software application idea, including product managers, technical founders, and engineering leads.

### Bottleneck

Turning an early idea into an implementable specification normally requires several engineering disciplines. A single generated document may look convincing while containing missing requirements, unprotected operations, undefined data entities, unmeasurable quality targets, or tests that do not cover the proposed behavior. A non-specialist often cannot detect these cross-document inconsistencies before development begins.

### User value

ArchitectOS produces a developer-ready blueprint and shows evidence that its requirements are represented across architecture, data, API, security, and testing artifacts. Unresolved assumptions and verification failures remain visible for human review.

## Submission Claim

> ArchitectOS turns an ambiguous software application idea into a verified engineering blueprint, with traceable evidence that each requirement is implemented and tested.

This claim will be accepted only if the final evaluation demonstrates improvement over the one-prompt baseline on the same cases and scoring rules.

## Evaluation Design

### Baseline

One direct Gemini prompt receives the project idea, the required output schema, and basic instructions. It produces all blueprint sections in a single response without specialist memory, verification tools, or repair iterations.

### Agent solution

ArchitectOS uses structured specialist artifacts, shared session context, deterministic verification, and targeted repair. The model family and evaluation cases should remain the same as the baseline. Any resource differences will be disclosed.

### Primary metric

**Verified Blueprint Coverage (VBC)**

```text
VBC = passed required verification checks / total required verification checks * 100
```

The checks cover:

1. Functional-requirement implementation coverage
2. Functional-requirement test coverage
3. Protected-operation authentication and authorization coverage
4. Cross-artifact reference integrity
5. Measurable NFRs with verification methods
6. Case-specific edge-case and risk coverage

### Secondary metrics

- Number of unresolved critical findings
- Human correction time per case
- End-to-end runtime
- Model calls and approximate cost per case
- Structured-output validity rate

### Fairness controls

- Use the same ten cases for baseline and final evaluation.
- Use the same model family unless a difference is explicitly documented.
- Give both systems the same required output schema.
- Freeze cases and scoring rules before implementation results are measured.
- Store every raw output, verifier report, runtime, and failure.
- Do not remove failed cases from aggregate results.

## Evaluation Cases

The frozen synthetic cases live in `evaluation/cases.json`. They cover common application categories and include one explicitly challenging case involving concurrency, offline synchronization, authorization, and data residency.

## Phase Gates

| Phase | Completion evidence |
|---|---|
| 0. Competition boundary | Pre-existing and competition work documented |
| 1. Evaluation design | Ten frozen cases and versioned rubric |
| 2. Baseline | Reproducible raw baseline results |
| 3. Shared context | Trajectory proves downstream artifact use |
| 4. Proof Graph | Deterministic evidence report |
| 5. Targeted repair | Real failure, repair, and re-verification trace |
| 6. User output | Exported blueprint suitable for developer handoff |
| 7. Final evaluation | Complete baseline-versus-agent results |
| 8. Submission | Clean reproduction and five-minute video |
