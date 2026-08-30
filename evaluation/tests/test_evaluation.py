import json
import tempfile
import unittest
from pathlib import Path

from evaluation.baseline import calculate_cost, load_cases, write_summary
from evaluation.models import Blueprint
from evaluation.scorer import score_blueprint


def valid_blueprint() -> Blueprint:
    return Blueprint.model_validate({
        "idea_summary": "A secure workspace that lets members create and review shared records.",
        "functional_requirements": [{
            "id": "FR-1",
            "statement": "Authorized members can create a workspace record.",
            "acceptance_criteria": ["A valid request persists one record."],
        }],
        "non_functional_requirements": [{
            "id": "NFR-1",
            "statement": "The create operation responds quickly under normal load.",
            "target": "p95 latency below 300 ms at 100 concurrent users",
            "verification_method": "Run a k6 load test for ten minutes.",
        }],
        "architecture_components": [{
            "id": "COMP-1",
            "name": "Workspace service",
            "responsibilities": ["Authorize and persist workspace records."],
            "requirement_ids": ["FR-1"],
            "entity_ids": ["ENT-1"],
        }],
        "data_entities": [{
            "id": "ENT-1",
            "name": "WorkspaceRecord",
            "purpose": "Stores an organization-scoped workspace record.",
            "sensitive": False,
        }],
        "api_operations": [{
            "id": "API-1",
            "method": "POST",
            "path": "/workspace-records",
            "purpose": "Create a workspace record.",
            "public": False,
            "authentication": "OAuth2 bearer token",
            "authorization": "Caller must be a workspace member.",
            "requirement_ids": ["FR-1"],
            "entity_ids": ["ENT-1"],
        }],
        "tests": [{
            "id": "TEST-1",
            "kind": "security",
            "description": "Reject an unauthenticated workspace record creation request.",
            "requirement_ids": ["FR-1"],
            "api_operation_ids": ["API-1"],
            "negative": True,
        }],
        "obligation_coverage": [{
            "obligation_id": "workspace_role_authorization",
            "design_response": "The API checks workspace membership before every write.",
            "evidence_ids": ["API-1", "TEST-1"],
        }],
        "assumptions": [{
            "id": "ASM-1",
            "statement": "Organization administrators manage workspace membership.",
            "needs_human_review": True,
        }],
    })


class EvaluationTests(unittest.TestCase):
    def test_case_set_is_frozen_and_has_ten_cases(self) -> None:
        cases = load_cases(Path("evaluation/cases.json"))
        self.assertTrue(cases.frozen)
        self.assertEqual(10, len(cases.cases))
        self.assertEqual(1, sum(case.challenging for case in cases.cases))

    def test_valid_blueprint_passes_core_checks(self) -> None:
        case = load_cases(Path("evaluation/cases.json")).cases[7]
        blueprint = valid_blueprint()
        blueprint.obligation_coverage = [
            {
                "obligation_id": obligation,
                "design_response": "The design includes a concrete control with linked evidence.",
                "evidence_ids": ["COMP-1", "API-1", "TEST-1"],
            }
            for obligation in case.obligations
        ]
        score = score_blueprint(blueprint, case)
        self.assertEqual(100.0, score["verified_blueprint_coverage"])
        self.assertTrue(score["ready"])

    def test_missing_security_is_critical(self) -> None:
        case = load_cases(Path("evaluation/cases.json")).cases[0]
        blueprint = valid_blueprint()
        blueprint.api_operations[0].authentication = None
        score = score_blueprint(blueprint, case)
        self.assertFalse(score["ready"])
        self.assertTrue(any(item["rule_id"] == "VBC-03" for item in score["critical_findings"]))

    def test_unknown_reference_fails(self) -> None:
        case = load_cases(Path("evaluation/cases.json")).cases[0]
        blueprint = valid_blueprint()
        blueprint.tests[0].api_operation_ids = ["API-999"]
        score = score_blueprint(blueprint, case)
        failed = [item for item in score["checks"] if not item["passed"]]
        self.assertTrue(any(item["rule_id"] == "VBC-06" for item in failed))

    def test_nfr_reference_is_valid(self) -> None:
        case = load_cases(Path("evaluation/cases.json")).cases[0]
        blueprint = valid_blueprint()
        blueprint.architecture_components[0].requirement_ids.append("NFR-1")
        score = score_blueprint(blueprint, case)
        matching = [
            item for item in score["checks"]
            if item["rule_id"] == "VBC-06" and item["subject_id"] == "COMP-1->NFR-1"
        ]
        self.assertEqual(1, len(matching))
        self.assertTrue(matching[0]["passed"])

    def test_vague_nfr_target_fails(self) -> None:
        case = load_cases(Path("evaluation/cases.json")).cases[0]
        blueprint = valid_blueprint()
        blueprint.non_functional_requirements[0].target = "The application should be fast"
        blueprint.non_functional_requirements[0].verification_method = "Review the result"
        score = score_blueprint(blueprint, case)
        failed = [item for item in score["checks"] if not item["passed"]]
        self.assertTrue(any(item["rule_id"] == "VBC-05" for item in failed))

    def test_test_obligation_requires_test_evidence(self) -> None:
        case = load_cases(Path("evaluation/cases.json")).cases[0]
        blueprint = valid_blueprint()
        blueprint.obligation_coverage = [{
            "obligation_id": "concurrent_booking_test",
            "design_response": "The architecture serializes competing booking requests.",
            "evidence_ids": ["COMP-1"],
        }]
        score = score_blueprint(blueprint, case)
        check = next(
            item for item in score["checks"]
            if item["rule_id"] == "VBC-08" and item["subject_id"] == "concurrent_booking_test"
        )
        self.assertFalse(check["passed"])

    def test_cost_requires_explicit_prices(self) -> None:
        self.assertIsNone(calculate_cost(100, 50, None, None))
        self.assertEqual(0.0002, calculate_cost(100, 50, 1.0, 2.0))

    def test_summary_preserves_failures(self) -> None:
        records = [
            {
                "case_id": "CASE-01",
                "status": "completed",
                "runtime_seconds": 1.0,
                "approximate_cost_usd": None,
                "score": {
                    "verified_blueprint_coverage": 75.0,
                    "critical_findings": [],
                },
            },
            {
                "case_id": "CASE-02",
                "status": "failed",
                "runtime_seconds": 0.5,
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            summary = write_summary(records, Path(directory))
            stored = json.loads((Path(directory) / "summary.json").read_text())
        self.assertEqual(1, summary["failed_cases"])
        self.assertEqual(50.0, summary["structured_output_validity_rate"])
        self.assertEqual(summary, stored)


if __name__ == "__main__":
    unittest.main()
