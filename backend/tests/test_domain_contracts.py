import unittest
from app.models.domain_contracts import (
    RequirementsContract,
    FunctionalRequirement,
    NonFunctionalRequirement,
    ArchitectureContract,
    ArchitectureComponent,
    DataContract,
    DatabaseTable,
    DatabaseColumn,
    ApiContract,
    ApiEndpoint,
    HttpMethod,
    QualityContract,
    TestCase,
    RiskContract,
    RiskFinding,
)


class DomainContractsTests(unittest.TestCase):
    def test_requirements_contract_validation(self):
        req = RequirementsContract(
            idea_summary="A real-time whiteboard app for engineering teams.",
            functional_requirements=[
                FunctionalRequirement(
                    id="FR-1",
                    statement="Users can create collaborative whiteboards.",
                    acceptance_criteria=["Board is assigned a unique UUID."]
                )
            ],
            non_functional_requirements=[
                NonFunctionalRequirement(
                    id="NFR-1",
                    statement="Real-time drawing updates must be low latency.",
                    target="< 50ms p95 latency",
                    verification_method="Run k6 WebSocket latency benchmark."
                )
            ]
        )
        self.assertEqual(len(req.functional_requirements), 1)
        self.assertEqual(req.functional_requirements[0].id, "FR-1")

    def test_architecture_contract_validation(self):
        arch = ArchitectureContract(
            topology_pattern="Modular Monolith with API Gateway",
            components=[
                ArchitectureComponent(
                    id="COMP-1",
                    name="Whiteboard Engine",
                    responsibilities=["Broadcast drawing updates."],
                    requirement_ids=["FR-1"]
                )
            ],
            authentication_strategy="OAuth2 with JWT token rotation",
            rate_limiting_strategy="Token Bucket on API Gateway",
            markdown_blueprint="# System Architecture\n..."
        )
        self.assertEqual(arch.components[0].id, "COMP-1")

    def test_data_contract_validation(self):
        data = DataContract(
            tables=[
                DatabaseTable(
                    table_name="whiteboards",
                    columns=[
                        DatabaseColumn(name="id", data_type="UUID", primary_key=True),
                        DatabaseColumn(name="creator_id", data_type="UUID", references="users(id)")
                    ],
                    purpose="Stores whiteboard session metadata."
                )
            ],
            ddl_sql="CREATE TABLE whiteboards (id UUID PRIMARY KEY);",
            markdown_blueprint="# Database Schema\n..."
        )
        self.assertEqual(data.tables[0].table_name, "whiteboards")

    def test_api_contract_validation(self):
        api = ApiContract(
            openapi_yaml="openapi: 3.0.0\npaths:\n  /api/v1/whiteboards:\n    post:\n      summary: Create board",
            endpoints=[
                ApiEndpoint(
                    id="API-1",
                    method=HttpMethod.POST,
                    path="/api/v1/whiteboards",
                    summary="Create a new whiteboard",
                    public=False,
                    security_scheme="OAuth2Bearer"
                )
            ],
            markdown_blueprint="# API Specification\n..."
        )
        self.assertEqual(api.endpoints[0].method, HttpMethod.POST)

    def test_quality_and_risk_contracts(self):
        quality = QualityContract(
            test_cases=[
                TestCase(
                    id="TEST-1",
                    kind="security",
                    description="Reject unauthenticated whiteboard creation requests.",
                    requirement_ids=["FR-1"],
                    negative=True
                )
            ],
            negative_test_count=1,
            markdown_blueprint="# Test Plan\n..."
        )
        self.assertTrue(quality.test_cases[0].negative)

        risk = RiskContract(
            vbc_score=96.0,
            readiness_score=96,
            release_ready=True,
            critical_findings=[],
            remediation_actions=[],
            markdown_blueprint="# Risk Report\n..."
        )
        self.assertTrue(risk.release_ready)
