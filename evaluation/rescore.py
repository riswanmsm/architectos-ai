import argparse
import json
from pathlib import Path

from evaluation.baseline import load_cases, write_summary
from evaluation.models import Blueprint
from evaluation.scorer import score_blueprint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recompute deterministic scores from preserved blueprint outputs."
    )
    parser.add_argument("results", type=Path)
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = {case.id: case for case in load_cases(args.cases).cases}
    records: list[dict] = []
    for run_path in sorted(args.results.glob("CASE-*/run.json")):
        record = json.loads(run_path.read_text(encoding="utf-8"))
        case_id = record.get("case_id")
        blueprint_path = run_path.parent / "blueprint.json"
        if record.get("status") == "completed" and case_id in cases and blueprint_path.exists():
            blueprint = Blueprint.model_validate_json(
                blueprint_path.read_text(encoding="utf-8")
            )
            score = score_blueprint(blueprint, cases[case_id])
            record["score"] = score
            (run_path.parent / "score.json").write_text(
                json.dumps(score, indent=2) + "\n",
                encoding="utf-8",
            )
            run_path.write_text(
                json.dumps(record, indent=2) + "\n",
                encoding="utf-8",
            )
        records.append(record)
    if not records:
        raise SystemExit(f"No case results found under {args.results}")
    summary = write_summary(records, args.results)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
