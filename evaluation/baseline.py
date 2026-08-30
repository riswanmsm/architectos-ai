import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

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


PROMPT_VERSION = "baseline-v1.0.0"


def load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE entries without overwriting the process environment."""
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


def build_prompt(case: EvaluationCase) -> str:
    obligations = "\n".join(f"- {item}" for item in case.obligations)
    return f"""You are a general-purpose software planning assistant.

Create a complete engineering blueprint for the application idea below in one response. Do not use tools, external context, specialist agents, iterative review, or self-correction. Return only data matching the required JSON schema.

Application idea:
{case.idea}

The blueprint must explicitly consider these case obligations:
{obligations}

Use stable IDs with these prefixes: FR-, NFR-, COMP-, ENT-, API-, TEST-, and ASM-. Link artifacts using those IDs. Public operations may use null authentication and authorization. Non-public operations must describe both. For every obligation, provide a design response and evidence IDs that point to artifacts in the blueprint. Record uncertain product decisions as assumptions needing human review.
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


def run_case(
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
    prompt = build_prompt(case)
    started_at = datetime.now(timezone.utc)
    start = time.perf_counter()

    record: dict = {
        "evaluation_version": EVALUATION_VERSION,
        "prompt_version": PROMPT_VERSION,
        "case_id": case.id,
        "provider": provider_name,
        "model": model,
        "started_at": started_at.isoformat(),
        "status": "failed",
    }
    (case_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    try:
        response = provider_client.generate_structured(prompt, Blueprint)
        raw_text = response.raw_text
        (case_dir / "raw_response.json").write_text(raw_text, encoding="utf-8")
        blueprint = Blueprint.model_validate_json(raw_text)
        (case_dir / "blueprint.json").write_text(
            json.dumps(blueprint.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        score = score_blueprint(blueprint, case)
        (case_dir / "score.json").write_text(
            json.dumps(score, indent=2) + "\n",
            encoding="utf-8",
        )

        input_tokens = response.input_tokens
        output_tokens = response.output_tokens
        record.update({
            "status": "completed",
            "request_id": response.request_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "approximate_cost_usd": calculate_cost(
                input_tokens,
                output_tokens,
                input_price_per_million,
                output_price_per_million,
            ),
            "score": score,
        })
    except (ValidationError, json.JSONDecodeError) as exc:
        record["error_type"] = type(exc).__name__
        record["error"] = str(exc)
    except Exception as exc:
        record["error_type"] = type(exc).__name__
        error = str(exc)
        for key_name in ("GEMINI_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY"):
            secret = os.getenv(key_name)
            if secret:
                error = error.replace(secret, "[REDACTED]")
        record["error"] = error
    finally:
        record["runtime_seconds"] = round(time.perf_counter() - start, 3)
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
        "system": "one_prompt_baseline",
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
    parser = argparse.ArgumentParser(description="Run the ArchitectOS one-prompt baseline.")
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
    if args.case_ids and len(selected) != len(set(args.case_ids)):
        known = {case.id for case in case_set.cases}
        missing = sorted(set(args.case_ids) - known)
        print(f"Unknown case IDs: {', '.join(missing)}", file=sys.stderr)
        return 2

    safe_run_name = re.sub(
        r"[^a-zA-Z0-9_.-]+",
        "-",
        f"{settings.provider_name}-{settings.model}",
    )
    output_dir = args.output or Path("evaluation/results/baseline") / safe_run_name
    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.overwrite:
        existing = [case.id for case in selected if (output_dir / case.id / "run.json").exists()]
        if existing:
            print(
                f"Existing results for {', '.join(existing)}. Use --overwrite or a new output directory.",
                file=sys.stderr,
            )
            return 2

    input_price = (
        args.input_price_per_million
        if args.input_price_per_million is not None
        else settings.pricing.input_price_per_million
    )
    output_price = (
        args.output_price_per_million
        if args.output_price_per_million is not None
        else settings.pricing.output_price_per_million
    )
    records = [
        run_case(
            provider_client,
            case,
            settings.provider_name,
            settings.model,
            output_dir,
            input_price,
            output_price,
        )
        for case in selected
    ]
    summary = write_summary(records, output_dir)
    print(json.dumps(summary, indent=2))
    return 0 if summary["failed_cases"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
