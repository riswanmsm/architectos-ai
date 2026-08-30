import unittest
from app.orchestrator.verifier import BlueprintVerifier
from app.orchestrator.coordinator import (
    start_session_instance,
    execute_step_instance,
    record_human_approval,
    export_session_trajectory
)
from app.models.schemas import StepRequest


class BackendOrchestratorTests(unittest.TestCase):
    def test_verifier_catches_missing_security(self):
        artifacts = {
            "requirements": "# Requirements\n- FR-1: User auth\n- NFR-1: 100ms latency",
            "architecture": "# System Architecture\nModular Monolith with placeholder auth and no rate-limiting.",
            "database": "# Database\nCREATE TABLE users (id UUID PRIMARY KEY);",
            "api": "# API\n/login:\n  post:\n    summary: Login",
            "testing": "# Tests\nJest unit test."
        }
        res = BlueprintVerifier.verify_artifacts(artifacts)
        self.assertFalse(res["ready"])
        self.assertLessEqual(res["readiness_score"], 78)
        self.assertTrue(len(res["critical_findings"]) > 0)
        self.assertTrue(any("rate-limiting" in f.lower() or "auth" in f.lower() for f in res["critical_findings"]))

    def test_verifier_passes_hardened_design(self):
        artifacts = {
            "requirements": "# Requirements\n- FR-1: User authentication\n- NFR-1: 100ms latency target p95",
            "architecture": "# System Architecture\nCOMP-1 API Gateway with Token Bucket rate-limiting and OAuth2 JWT authentication (maps to FR-1).",
            "database": "# Database\nCREATE TABLE users (id UUID PRIMARY KEY);",
            "api": "# API\n/api/v1/workspaces:\n  post:\n    summary: Workspace creation (FR-1)\n    security:\n      - OAuth2Bearer: []",
            "testing": "# Tests\nTEST-1 unit for FR-1, TEST-2 Playwright integration, TEST-3 k6 load under 100ms, TEST-4 negative unauthorized token rejection."
        }
        res = BlueprintVerifier.verify_artifacts(artifacts)
        self.assertTrue(res["ready"])
        self.assertGreaterEqual(res["readiness_score"], 90)
        self.assertEqual(len(res["critical_findings"]), 0)

    def test_full_session_lifecycle_and_trajectory(self):
        idea = "A decentralized collaborative document editor with versioning and role-based access"
        session_info = start_session_instance(idea)
        session_id = session_info["session_id"]
        
        # Step 1: Requirements
        req_res = execute_step_instance(StepRequest(session_id=session_id, step_id="requirements", idea=idea))
        self.assertEqual(req_res["status"], "completed")

        # Step 2: Architecture
        arch_res = execute_step_instance(StepRequest(session_id=session_id, step_id="architecture", idea=idea))
        self.assertEqual(arch_res["status"], "completed")

        # Step 3: Database
        db_res = execute_step_instance(StepRequest(session_id=session_id, step_id="database", idea=idea))
        self.assertEqual(db_res["status"], "completed")

        # Step 4: API
        api_res = execute_step_instance(StepRequest(session_id=session_id, step_id="api", idea=idea))
        self.assertEqual(api_res["status"], "completed")

        # Step 5: Testing
        test_res = execute_step_instance(StepRequest(session_id=session_id, step_id="testing", idea=idea))
        self.assertEqual(test_res["status"], "completed")

        # Step 6: Risk (First pass catches missing security in initial draft)
        risk_res = execute_step_instance(StepRequest(session_id=session_id, step_id="risk", idea=idea))
        self.assertEqual(risk_res["status"], "failed")
        self.assertLessEqual(risk_res["readiness_score"], 80)

        # Step 7: Architecture Retry (Self-correction)
        retry_res = execute_step_instance(StepRequest(session_id=session_id, step_id="architecture_retry", idea=idea))
        self.assertEqual(retry_res["status"], "completed")

        # Step 8: Risk Retry (Promoted)
        risk_retry_res = execute_step_instance(StepRequest(session_id=session_id, step_id="risk_retry", idea=idea))
        self.assertEqual(risk_retry_res["status"], "completed")
        self.assertGreaterEqual(risk_retry_res["readiness_score"], 90)

        # Human Approval Gate
        approval_res = record_human_approval(session_id, approved=True, notes="Lead Architect signed off on OAuth2 token rotation.")
        self.assertEqual(approval_res["status"], "success")

        # Trajectory Export
        trajectory = export_session_trajectory(session_id)
        self.assertGreaterEqual(trajectory["total_steps"], 8)
        self.assertEqual(len(trajectory["human_checkpoints"]), 1)
