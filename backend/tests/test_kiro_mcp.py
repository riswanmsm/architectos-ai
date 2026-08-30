import unittest
import zipfile
import io
from app.orchestrator.coordinator import (
    start_session_instance,
    execute_step_instance,
    record_human_approval,
    sessions,
)
from app.models.schemas import StepRequest
from app.orchestrator.kiro_exporter import (
    format_kiro_specs,
    create_kiro_zip_archive,
)
from app.mcp.tool_registry import MCP_TOOLS
from app.mcp.server import call_mcp_tool, ToolCallRequest


class KiroAndMcpIntegrationTests(unittest.TestCase):
    def test_kiro_spec_formatting_and_zip(self):
        artifacts = {
            "requirements": "# Requirements\n- FR-1: Scope\n- NFR-1: Fast",
            "architecture": "# System Architecture\nModular Monolith with API Gateway",
            "database": "CREATE TABLE users (id UUID PRIMARY KEY);",
            "api": "openapi: 3.0.0\npaths: /login:",
            "testing": "# Tests\nJest unit tests."
        }
        verifier_summary = {
            "vbc_score": 96.0,
            "ready": True,
            "critical_findings": []
        }
        specs = format_kiro_specs(artifacts, verifier_summary)
        
        self.assertIn(".kiro/specs/requirements.md", specs)
        self.assertIn(".kiro/specs/architecture.md", specs)
        self.assertIn(".kiro/specs/schema.sql", specs)
        self.assertIn(".kiro/specs/api.yaml", specs)
        self.assertIn(".kiro/specs/test-matrix.md", specs)
        self.assertIn(".kiro/specs/risk-audit.md", specs)
        self.assertIn("96.0%", specs[".kiro/specs/risk-audit.md"])

        # Test ZIP generation
        zip_buffer = create_kiro_zip_archive(specs)
        self.assertGreater(zip_buffer.getbuffer().nbytes, 0)
        
        with zipfile.ZipFile(zip_buffer, "r") as z:
            names = z.namelist()
            self.assertEqual(len(names), 6)
            self.assertIn(".kiro/specs/schema.sql", names)

    def test_mcp_tool_list(self):
        self.assertEqual(len(MCP_TOOLS), 3)
        tool_names = [t["name"] for t in MCP_TOOLS]
        self.assertIn("architectos_generate_blueprint", tool_names)
        self.assertIn("architectos_verify_spec", tool_names)
        self.assertIn("architectos_audit_risk", tool_names)

    def test_mcp_verify_spec_execution(self):
        req = ToolCallRequest(
            name="architectos_verify_spec",
            arguments={
                "requirements": "# Requirements\n- FR-1: Scope\n- NFR-1: 100ms latency p95 target",
                "architecture": "COMP-1 API Gateway with rate-limiting and OAuth2 JWT (maps to FR-1)",
                "database": "CREATE TABLE users (id UUID PRIMARY KEY);",
                "api": "/api/v1/users:\n  post:\n    security: [OAuth2Bearer: []]",
                "testing": "TEST-1 unit, TEST-2 negative unauthorized rejection under 100ms"
            }
        )
        res = call_mcp_tool(req)
        self.assertIn("verification_result", res)
        self.assertTrue(res["verification_result"]["ready"])

    def test_mcp_audit_risk_execution(self):
        req = ToolCallRequest(
            name="architectos_audit_risk",
            arguments={
                "architecture_spec": "Modular Monolith with placeholder auth and no rate-limiting.",
                "api_spec": "/login:\n  post:\n    summary: Login"
            }
        )
        res = call_mcp_tool(req)
        self.assertFalse(res["audit_passed"])
        self.assertGreater(len(res["critical_findings"]), 0)

    def test_mcp_generate_blueprint_execution(self):
        idea = "A simple task tracking board for small development teams"
        req = ToolCallRequest(
            name="architectos_generate_blueprint",
            arguments={"idea": idea}
        )
        res = call_mcp_tool(req)
        self.assertIn("kiro_specs", res)
        self.assertIn(".kiro/specs/requirements.md", res["kiro_specs"])
        self.assertGreaterEqual(res["readiness_score"], 90)
