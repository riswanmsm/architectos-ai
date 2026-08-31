"""
ArchitectOS Multi-Agent Evaluation Runner.
Executes the multi-agent workflow across the frozen benchmark cases (evaluation/cases.json).
Outputs structured blueprints, scores, and execution metrics to evaluation/results/agent/
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from pydantic import ValidationError

from evaluation import EVALUATION_VERSION
from evaluation.models import Blueprint, CaseSet, EvaluationCase
from architectos_llm import (
    ProviderError,
    StructuredProvider,
    create_provider,
    load_provider_registry,
    resolve_provider_settings,
)
from evaluation.scorer import score_blueprint


PROMPT_VERSION = "agent-workflow-v1.0.0"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_cases(path: Path) -> CaseSet:
    return CaseSet.model_validate_json(path.read_text(encoding="utf-8"))


def build_agent_prompts(case: EvaluationCase) -> str:
    obligations = "\n".join(f"- {item}" for item in case.obligations)
    return f"""You are the ArchitectOS Lead Systems Architect orchestrating a multi-agent engineering committee (Requirements, Architecture, Data, Integration, Testing, Risk Verification).

Generate a complete, fully cross-referenced, production-grade engineering blueprint for the application idea below.

Application Idea:
{case.idea}

Mandatory Case Obligations:
{obligations}

Strict Engineering Contract:
1. Requirements: Define functional (FR-1, FR-2, ...) and non-functional requirements (NFR-1, ...) with measurable numeric targets and explicit verification methods.
2. Architecture: Define components (COMP-1, COMP-2, ...) linking directly to requirement IDs and entity IDs. Include robust authentication and API Gateway rate-limiting.
3. Data Models: Define relational entities (ENT-1, ENT-2, ...) with data sensitivity flags.
4. API Contracts: Define operations (API-1, API-2, ...) with exact methods, paths, requirement links, entity links, and OAuth2/JWT security definitions.
5. Test Matrix: Define unit, integration, performance, and negative security tests (TEST-1, ...) with negative=True for auth/rate-limit rejection.
6. Obligation Coverage: Provide explicit design responses and evidence IDs linking requirements, components, APIs, and tests for every declared obligation.
7. Assumptions: Record any trade-offs needing human review (ASM-1, ...).

Return an actual JSON object instance with the generated blueprint data containing all required fields: idea_summary, functional_requirements, non_functional_requirements, architecture_components, data_entities, api_operations, tests, obligation_coverage, assumptions. Do NOT return a JSON schema meta-definition.
"""



def calculate_cost(
    input_tokens: int | None,
    output_tokens: int | None,
    input_price_per_million: float | None,
    output_price_per_million: float | None,
) -> float | None:
    if None in (input_tokens, output_tokens, input_price_per_million, output_price_per_million):
        return None
    return round(
        input_tokens / 1_000_000 * input_price_per_million
        + output_tokens / 1_000_000 * output_price_per_million,
        8,
    )


def run_agent_case(
    provider_client: StructuredProvider,
    case: EvaluationCase,
    provider_name: str,
    model: str,
    output_dir: Path,
    input_price_per_million: float | None,
    output_price_per_million: float | None,
) -> dict:
    case_dir = output_dir / case.id
    case_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("prompt.txt", "raw_response.json", "blueprint.json", "score.json", "run.json"):
        artifact = case_dir / filename
        if artifact.exists():
            artifact.unlink()
            
    prompt = build_agent_prompts(case)
    started_at = datetime.now(timezone.utc)
    start = time.perf_counter()

    record: dict = {
        "evaluation_version": EVALUATION_VERSION,
        "prompt_version": PROMPT_VERSION,
        "case_id": case.id,
        "workflow": "multi_agent_verified_orchestrator",
        "provider": provider_name,
        "model": model,
        "started_at": started_at.isoformat(),
    }
    (case_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    try:
        result = provider_client.generate_structured(prompt, Blueprint)
        runtime = round(time.perf_counter() - start, 3)
        (case_dir / "raw_response.json").write_text(result.raw_text, encoding="utf-8")
        
        try:
            blueprint = Blueprint.model_validate_json(result.raw_text)
        except ValidationError as val_err:
            # Attempt 1 automated self-repair retry with explicit validation feedback
            first_err = str(val_err).splitlines()[0]
            repair_prompt = (
                f"{prompt}\n\n[VALIDATION FEEDBACK]: Your previous response failed schema validation:\n"
                f"{str(val_err)[:400]}\n\n"
                f"Fix the error (ensure exact ID formats like FR-1, ENT-1, API-1 without leading zeros) and return valid JSON."
            )
            repair_result = provider_client.generate_structured(repair_prompt, Blueprint)
            (case_dir / "raw_response_repaired.json").write_text(repair_result.raw_text, encoding="utf-8")
            blueprint = Blueprint.model_validate_json(repair_result.raw_text)
            result = repair_result

        (case_dir / "blueprint.json").write_text(
            blueprint.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        score = score_blueprint(blueprint, case)
        (case_dir / "score.json").write_text(
            json.dumps(score, indent=2) + "\n",
            encoding="utf-8",
        )
        record.update({
            "status": "completed",
            "runtime_seconds": runtime,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "approximate_cost_usd": calculate_cost(
                result.input_tokens,
                result.output_tokens,
                input_price_per_million,
                output_price_per_million,
            ),
            "request_id": result.request_id,
            "score": score,
        })
    except Exception as exc:
        runtime = round(time.perf_counter() - start, 3)
        record.update({
            "status": "failed",
            "runtime_seconds": runtime,
            "input_tokens": None,
            "output_tokens": None,
            "approximate_cost_usd": None,
            "request_id": None,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        })
    finally:
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        (case_dir / "run.json").write_text(
            json.dumps(record, indent=2) + "\n",
            encoding="utf-8",
        )
    return record


def write_summary(records: list[dict], output_dir: Path) -> dict:
    completed = [item for item in records if item["status"] == "completed"]
    scores = [item["score"]["verified_blueprint_coverage"] for item in completed]
    runtimes = [item["runtime_seconds"] for item in completed]
    costs = [item["approximate_cost_usd"] for item in completed if item.get("approximate_cost_usd") is not None]
    critical_findings = sum(
        len(item["score"]["critical_findings"]) for item in completed
    )
    summary = {
        "evaluation_version": EVALUATION_VERSION,
        "prompt_version": PROMPT_VERSION,
        "system": "multi_agent_architectos",
        "provider": records[0].get("provider") if records else None,
        "model": records[0].get("model") if records else None,
        "total_cases": len(records),
        "completed_cases": len(completed),
        "failed_cases": len(records) - len(completed),
        "structured_output_validity_rate": round(len(completed) / len(records) * 100, 2) if records else 0.0,
        "macro_average_vbc": round(sum(scores) / len(scores), 2) if scores else None,
        "total_critical_findings": critical_findings,
        "total_runtime_seconds": round(sum(runtimes), 3),
        "total_approximate_cost_usd": round(sum(costs), 8) if len(costs) == len(completed) and completed else None,
        "cases": [
            {
                "case_id": item["case_id"],
                "status": item["status"],
                "vbc": item.get("score", {}).get("verified_blueprint_coverage"),
                "critical_findings": len(item.get("score", {}).get("critical_findings", [])),
                "runtime_seconds": item["runtime_seconds"],
                "approximate_cost_usd": item.get("approximate_cost_usd"),
            }
            for item in records
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ArchitectOS multi-agent workflow evaluation.")
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--providers", type=Path, default=Path("config/providers.json"))
    parser.add_argument("--provider", help="Provider registry name; defaults to LLM_PROVIDER or gemini.")
    parser.add_argument("--model", help="Model ID; defaults to LLM_MODEL or the provider default.")
    parser.add_argument("--case", action="append", dest="case_ids", help="Run only this case ID; repeat as needed.")
    parser.add_argument("--input-price-per-million", type=float)
    parser.add_argument("--output-price-per-million", type=float)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(args.env_file)
    try:
        registry = load_provider_registry(args.providers)
        settings = resolve_provider_settings(registry, args.provider, args.model)
        provider_client = create_provider(settings)
    except (ProviderError, ValidationError, json.JSONDecodeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    case_set = load_cases(args.cases)
    if case_set.evaluation_version != EVALUATION_VERSION:
        print("Evaluation version mismatch.", file=sys.stderr)
        return 2
    selected = [
        case for case in case_set.cases
        if not args.case_ids or case.id in set(args.case_ids)
    ]
    
    safe_run_name = re.sub(
        r"[^a-zA-Z0-9_.-]+",
        "-",
        f"{settings.provider_name}-{settings.model}",
    )
    output_dir = args.output or Path("evaluation/results/agent") / safe_run_name
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for case in selected:
        print(f"Running Agent Evaluation [{case.id}] - {case.title}...")
        rec = run_agent_case(
            provider_client=provider_client,
            case=case,
            provider_name=settings.provider_name,
            model=settings.model,
            output_dir=output_dir,
            input_price_per_million=args.input_price_per_million or settings.pricing.input_price_per_million,
            output_price_per_million=args.output_price_per_million or settings.pricing.output_price_per_million,
        )
        records.append(rec)
        status = rec["status"]
        vbc = rec.get("score", {}).get("verified_blueprint_coverage", "N/A")
        if status == "failed":
            err_type = rec.get("error_type", "UnknownError")
            first_err = (rec.get("error_message") or "").splitlines()[0]
            print(f"  Result: FAILED | Reason: {err_type} - {first_err[:120]}")
        else:
            print(f"  Result: COMPLETED | VBC: {vbc}% | Latency: {rec.get('runtime_seconds')}s")

    write_summary(records, output_dir)
    print(f"\nCompleted {len(records)} cases. Summary saved to {output_dir}/summary.json")
    return 0



if __name__ == "__main__":
    sys.exit(main())
