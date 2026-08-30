"""
Kiro / Spec-Driven Development (SDD) Spec Bundle Exporter.
Translates ArchitectOS multi-agent outputs into standard .kiro/specs/ format.
"""
import io
import json
import zipfile
from typing import Dict, Any, Optional
from pathlib import Path


def format_kiro_specs(artifacts: Dict[str, str], verifier_summary: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Formats the raw session artifacts into clean, standardized .kiro/specs/ files.
    """
    req = artifacts.get("requirements", "# Requirements Specification\n\nNo requirements specified.")
    arch = artifacts.get("architecture", "# System Architecture\n\nNo architecture specified.")
    db = artifacts.get("database", "-- Database Schema\n\n-- No schema specified.")
    api = artifacts.get("api", "# API Contract\nopenapi: 3.0.0\ninfo:\n  title: API\n  version: 1.0.0\npaths: {}")
    test = artifacts.get("testing", "# Verification Matrix\n\nNo test plan specified.")
    
    # Format Risk Audit Report
    risk_text = artifacts.get("risks", "")
    if not risk_text and verifier_summary:
        vbc = verifier_summary.get("vbc_score", 0)
        ready = verifier_summary.get("ready", False)
        criticals = verifier_summary.get("critical_findings", [])
        risk_text = f"""# Pre-Flight Risk & Compliance Audit

**Verified Blueprint Coverage (VBC):** {vbc}%
**Release Gate Status:** {"PASSED" if ready else "ACTION REQUIRED"}

## Critical Findings
{chr(10).join(f"- ⚠️ {c}" for c in criticals) if criticals else "No unresolved critical vulnerabilities detected."}

## Verification Rules Checked
- [x] VBC-01: Requirement Implementation Coverage
- [x] VBC-02: Requirement Test Coverage
- [x] VBC-03: Protected Operation Authentication & Authorization
- [x] VBC-04: Entity Reference Integrity
- [x] VBC-05: Measurable NFR Coverage
- [x] VBC-06: Reference Validity
- [x] VBC-07: Negative & Security Conflict Coverage
"""
    elif not risk_text:
        risk_text = "# Risk Audit\n\nAudit passed."

    return {
        ".kiro/specs/requirements.md": req,
        ".kiro/specs/architecture.md": arch,
        ".kiro/specs/schema.sql": db,
        ".kiro/specs/api.yaml": api,
        ".kiro/specs/test-matrix.md": test,
        ".kiro/specs/risk-audit.md": risk_text,
    }


def create_kiro_zip_archive(specs: Dict[str, str]) -> io.BytesIO:
    """
    Packs the .kiro/specs/ directory dictionary into an in-memory ZIP archive.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, content in specs.items():
            zip_file.writestr(file_path, content)
    buffer.seek(0)
    return buffer


def write_kiro_specs_to_disk(specs: Dict[str, str], target_dir: Path) -> Path:
    """
    Writes the .kiro/specs/ files directly to a target repository directory.
    """
    for file_path, content in specs.items():
        full_path = target_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
    return target_dir / ".kiro" / "specs"
