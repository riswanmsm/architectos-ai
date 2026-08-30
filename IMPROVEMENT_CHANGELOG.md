# Improvement Changelog

This changelog records competition experiments performed after pre-event commit `714b994`. Evidence links point to evaluation artifacts and test suites in the repository.

| Stage | What We Tried and Why | Evidence | Decision / Learning | Status |
|---|---|---|---|---|
| **Pre-event system** | Eight specialist personas generated blueprint sections in sequence, with a fixed risk rejection and retry for demonstration. | Repository at `714b994` | Established the starting point. Exposed that displayed confidence and readiness scores were hardcoded rather than evidence-derived. | Complete |
| **Provider abstraction** | Normalized Gemini, OpenAI-compatible, DeepSeek, and Anthropic calls so provider choice is configuration rather than orchestration logic. | 18 offline tests (`evaluation/tests/test_providers.py`); Gemini 3.7 Flash smoke test under `evaluation/results/baseline/` | **Kept.** Isolated Gemini schema quirks while preserving local Pydantic schema validation across all providers. | Complete |
| **Baseline** | One direct prompt with the same idea, obligations, and output schema to establish a baseline for a single LLM call without specialist agents. | `evaluation/baseline.py`, 10 frozen cases in `evaluation/cases.json` | Established baseline metrics. Single-prompt generation misses cross-cutting security constraints and test mappings on complex cases. | Complete |
| **Iteration 1 (Shared Structured Context)** | Downstream specialists consume upstream artifacts (Requirements feed Architecture; Architecture feeds Data and API; all feed Testing). | `backend/app/agents/specialists.py` context ingestion parameters | **Kept.** Eliminated naming and entity mismatch between requirements, API endpoints, and database models. | Complete |
| **Iteration 2 (Deterministic Cross-Artifact Verifier)** | Implemented a deterministic verifier (`backend/app/orchestrator/verifier.py`) enforcing VBC-01 to VBC-08 rules to derive real readiness scores. | `backend/tests/test_backend.py` unit suite; `evaluation/scorer.py` | **Kept.** Replaced hardcoded readiness with empirical VBC percentage and automated detection of critical security findings. | Complete |
| **Iteration 3 (Targeted Self-Correction Loop)** | When verification finds critical gaps (e.g., missing API rate-limiting or unmapped tests), feedback triggers targeted repair of only the affected discipline. | `backend/app/orchestrator/coordinator.py` self-correction loop | **Kept.** Increased Verified Blueprint Coverage from 66% on first draft to 96%+ upon repair without rerunning the entire pipeline. | Complete |
| **Removed Experiment (Unconstrained Multi-Agent Debate)** | Tested allowing Requirements, Architecture, and Risk agents to engage in a 3-turn open-ended debate before producing specs. | Experimental branch logs; token trace analysis | **Removed.** Tripled execution latency (from 25s to 85s) and token cost by 3.8x with no measurable improvement in VBC. Agents repeated generic platitudes rather than fixing concrete schema inconsistencies. Replaced by strict structured handoffs and deterministic rule checks. | Removed |
| **Final Solution** | Combined shared structured context, deterministic verification, targeted repair loop, and human architect approval checkpoint. | `evaluation/results/`, `trajectories/`, `backend/tests/` | Identifies the main contribution: deterministic verification + targeted repair outperforms unconstrained agent debate in both accuracy and token efficiency. | Complete |

---

## Entry Requirements

For each experiment conducted:
- **Hypothesis:** Structured context + deterministic verifiers provide higher reliability and traceability than single-prompt or open-ended multi-agent systems.
- **Exact Code Changes:** Added `BlueprintVerifier` in `backend/app/orchestrator/verifier.py`, updated `coordinator.py` with dynamic feedback loops and `TrajectoryTracker`, and added `evaluation/run_agent_eval.py` and `evaluation/compare.py`.
- **Evaluation Version & Cases:** `evaluation/cases.json` (Frozen Version 1.0.0, 10 benchmark cases).
- **Cost & Runtime:** Median runtime per case ~22s, approx cost < $0.05/run with Gemini Flash.
- **Decision:** Kept deterministic verifier and sequential pipeline; removed unconstrained multi-turn debate.

---

## Main Failure Mode and Hot Take

### Main Failure Mode: *The "Fluent Hallucination" Trap in Multi-Agent Specs*
When specialist LLMs generate documentation independently, each document sounds authoritative and fluent in isolation, but they silently diverge: API paths reference database entities that do not exist in the DDL, non-functional requirements lack measurable metrics, and protected endpoints lack explicit authorization boundaries. Without deterministic cross-reference validation, multi-agent systems produce convincing-looking but fundamentally broken specifications.

### Hot Take
> **"More agents $\neq$ better software blueprints.** Unconstrained multi-agent debate increases latency and token expenditure while compounding structural drift. The winning formula for reliable engineering agents is **strict domain specialization + shared structured context + deterministic rule verification + targeted repair loops.**"
