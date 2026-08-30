"""
ArchitectOS Evaluation Comparison Engine.
Compares Baseline vs Multi-Agent evaluations across the 10 benchmark cases.
Outputs side-by-side metric tables (VBC, critical findings, latency, cost).
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def format_table(baseline_summary: Dict[str, Any], agent_summary: Dict[str, Any]) -> str:
    b_vbc = baseline_summary.get("macro_average_vbc", 0.0) or 0.0
    a_vbc = agent_summary.get("macro_average_vbc", 0.0) or 0.0
    vbc_delta = round(a_vbc - b_vbc, 2)
    vbc_sign = "+" if vbc_delta > 0 else ""

    b_crit = baseline_summary.get("total_critical_findings", 0)
    a_crit = agent_summary.get("total_critical_findings", 0)
    crit_delta = a_crit - b_crit
    crit_sign = "+" if crit_delta > 0 else ""

    b_valid = baseline_summary.get("structured_output_validity_rate", 0.0)
    a_valid = agent_summary.get("structured_output_validity_rate", 0.0)

    b_cost = baseline_summary.get("total_approximate_cost_usd", 0.0) or 0.0
    a_cost = agent_summary.get("total_approximate_cost_usd", 0.0) or 0.0

    b_time = baseline_summary.get("total_runtime_seconds", 0.0) or 0.0
    a_time = agent_summary.get("total_runtime_seconds", 0.0) or 0.0

    table = f"""# ArchitectOS — Evaluation Comparison Report

## Aggregate Benchmark Performance

| Evaluation Metric | One-Prompt Baseline | ArchitectOS (Agent Workflow) | Delta |
| :--- | :---: | :---: | :---: |
| **Macro-Average VBC (%)** | **{b_vbc:.1f}%** | **{a_vbc:.1f}%** | **{vbc_sign}{vbc_delta:.1f}%** |
| **Total Critical Security Findings** | **{b_crit}** | **{a_crit}** | **{crit_sign}{crit_delta}** |
| **Structured Output Validity** | {b_valid:.1f}% | {a_valid:.1f}% | {a_valid - b_valid:+.1f}% |
| **Total Benchmark Runtime** | {b_time:.1f}s | {a_time:.1f}s | {a_time - b_time:+.1f}s |
| **Total Token Cost (USD)** | ${b_cost:.4f} | ${a_cost:.4f} | +${a_cost - b_cost:.4f} |

---

## Per-Case Breakdown

| Case ID | Status (Baseline / Agent) | VBC Baseline | VBC Agent | Delta | Baseline Criticals | Agent Criticals |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    baseline_cases = {c["case_id"]: c for c in baseline_summary.get("cases", [])}
    agent_cases = {c["case_id"]: c for c in agent_summary.get("cases", [])}
    all_case_ids = sorted(list(set(baseline_cases.keys()).union(agent_cases.keys())))

    for cid in all_case_ids:
        b_c = baseline_cases.get(cid, {})
        a_c = agent_cases.get(cid, {})
        
        b_s = b_c.get("status", "N/A")
        a_s = a_c.get("status", "N/A")
        status_pair = f"{b_s} / {a_s}"

        b_v = b_c.get("vbc")
        a_v = a_c.get("vbc")
        b_v_str = f"{b_v:.1f}%" if b_v is not None else "N/A"
        a_v_str = f"{a_v:.1f}%" if a_v is not None else "N/A"
        
        if b_v is not None and a_v is not None:
            d_v = f"{a_v - b_v:+.1f}%"
        else:
            d_v = "N/A"

        b_cf = b_c.get("critical_findings", 0)
        a_cf = a_c.get("critical_findings", 0)

        table += f"| **{cid}** | {status_pair} | {b_v_str} | **{a_v_str}** | **{d_v}** | {b_cf} | **{a_cf}** |\n"

    table += "\n> Note: VBC = Verified Blueprint Coverage. Critical findings prevent production release readiness regardless of score.\n"
    return table


def main():
    parser = argparse.ArgumentParser(description="Compare Baseline vs Agent evaluations.")
    parser.add_argument("--baseline", type=Path, help="Path to baseline summary.json")
    parser.add_argument("--agent", type=Path, help="Path to agent summary.json")
    parser.add_argument("--output", type=Path, help="Path to write markdown comparison report")
    args = parser.parse_args()

    baseline_path = args.baseline
    agent_path = args.agent

    # Auto-discover if not provided
    if not baseline_path:
        candidates = list(Path("evaluation/results/baseline").glob("*/summary.json"))
        if candidates:
            baseline_path = candidates[0]
    if not agent_path:
        candidates = list(Path("evaluation/results/agent").glob("*/summary.json"))
        if candidates:
            agent_path = candidates[0]

    if not baseline_path or not baseline_path.exists():
        print("Warning: Baseline summary not found. Run baseline.py first.")
        b_summary = {"macro_average_vbc": 0.0, "total_critical_findings": 0, "cases": []}
    else:
        b_summary = load_json(baseline_path) or {}

    if not agent_path or not agent_path.exists():
        print("Warning: Agent summary not found. Run run_agent_eval.py first.")
        a_summary = {"macro_average_vbc": 0.0, "total_critical_findings": 0, "cases": []}
    else:
        a_summary = load_json(agent_path) or {}

    report = format_table(b_summary, a_summary)
    print(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Report saved to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
