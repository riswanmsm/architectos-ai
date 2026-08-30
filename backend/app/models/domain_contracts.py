"""
Typed Domain Contracts for ArchitectOS Agent System.
Enforces strict Pydantic serialization and boundaries between isolated specialist agents.
"""
from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictContract(BaseModel):
    """Base model enforcing strict schema validation and forbidding extra undocumented fields."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class FunctionalRequirement(StrictContract):
    id: str = Field(..., pattern=r"^FR-[1-9][0-9]*$", description="Unique requirement ID (e.g. FR-1)")
    statement: str = Field(..., min_length=10, description="Clear description of functional capability")
    acceptance_criteria: List[str] = Field(..., min_length=1, description="Concrete validation criteria")


class NonFunctionalRequirement(StrictContract):
    id: str = Field(..., pattern=r"^NFR-[1-9][0-9]*$", description="Unique NFR ID (e.g. NFR-1)")
    statement: str = Field(..., min_length=10, description="Quality attribute description")
    target: str = Field(..., min_length=3, description="Measurable numeric target (e.g. < 100ms p95 latency)")
    verification_method: str = Field(..., min_length=5, description="Explicit test or benchmark method")


class RequirementsContract(StrictContract):
    """Output contract from Requirements Engineering Specialist."""
    idea_summary: str = Field(..., min_length=10)
    functional_requirements: List[FunctionalRequirement] = Field(..., min_length=1)
    non_functional_requirements: List[NonFunctionalRequirement] = Field(..., min_length=1)
    assumptions: List[str] = Field(default_factory=list)


class ArchitectureComponent(StrictContract):
    id: str = Field(..., pattern=r"^COMP-[1-9][0-9]*$", description="Component ID (e.g. COMP-1)")
    name: str = Field(..., min_length=2)
    responsibilities: List[str] = Field(..., min_length=1)
    requirement_ids: List[str] = Field(..., description="Linked functional requirement IDs")
    entity_ids: List[str] = Field(default_factory=list, description="Linked data entity names/IDs")


class ArchitectureContract(StrictContract):
    """Output contract from Architecture Engineering Specialist."""
    topology_pattern: str = Field(..., description="e.g. Modular Monolith, Event-Driven Microservices")
    components: List[ArchitectureComponent] = Field(..., min_length=1)
    authentication_strategy: str = Field(..., min_length=5, description="e.g. OAuth2 with JWT token rotation")
    rate_limiting_strategy: str = Field(..., min_length=5, description="e.g. Token Bucket on API Gateway")
    markdown_blueprint: str = Field(..., description="Renderable markdown specifications")


class DatabaseColumn(StrictContract):
    name: str
    data_type: str
    primary_key: bool = False
    nullable: bool = True
    references: Optional[str] = None
    is_sensitive: bool = False


class DatabaseTable(StrictContract):
    table_name: str = Field(..., min_length=2)
    columns: List[DatabaseColumn] = Field(..., min_length=1)
    purpose: str = Field(..., min_length=5)


class DataContract(StrictContract):
    """Output contract from Data Engineering Specialist."""
    tables: List[DatabaseTable] = Field(..., min_length=1)
    ddl_sql: str = Field(..., min_length=10, description="PostgreSQL compliant CREATE TABLE scripts")
    sensitive_data_classification: List[str] = Field(default_factory=list)
    markdown_blueprint: str = Field(..., description="Renderable markdown specifications")


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class ApiEndpoint(StrictContract):
    id: str = Field(..., pattern=r"^API-[1-9][0-9]*$")
    method: HttpMethod
    path: str = Field(..., pattern=r"^/")
    summary: str
    public: bool
    security_scheme: Optional[str] = None
    requirement_ids: List[str] = Field(default_factory=list)
    entity_ids: List[str] = Field(default_factory=list)
    expected_status_codes: List[int] = Field(default_factory=lambda: [200, 400, 401, 500])


class ApiContract(StrictContract):
    """Output contract from Integration Engineering Specialist."""
    openapi_yaml: str = Field(..., min_length=10, description="Valid OpenAPI 3.0 YAML specification")
    endpoints: List[ApiEndpoint] = Field(..., min_length=1)
    markdown_blueprint: str = Field(..., description="Renderable markdown specifications")


class TestCase(StrictContract):
    id: str = Field(..., pattern=r"^TEST-[1-9][0-9]*$")
    kind: Literal["unit", "integration", "e2e", "performance", "security"]
    description: str = Field(..., min_length=10)
    requirement_ids: List[str] = Field(..., min_length=1)
    negative: bool = False


class QualityContract(StrictContract):
    """Output contract from Quality Engineering Specialist."""
    test_cases: List[TestCase] = Field(..., min_length=1)
    frameworks: List[str] = Field(default_factory=lambda: ["Jest", "Playwright", "k6"])
    negative_test_count: int = Field(..., ge=0)
    markdown_blueprint: str = Field(..., description="Renderable markdown specifications")


class RiskFinding(StrictContract):
    rule_id: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    message: str
    remediation: str


class RiskContract(StrictContract):
    """Output contract from Risk Engineering Specialist."""
    vbc_score: float = Field(..., ge=0.0, le=100.0)
    readiness_score: int = Field(..., ge=0, le=100)
    release_ready: bool
    critical_findings: List[RiskFinding] = Field(default_factory=list)
    remediation_actions: List[str] = Field(default_factory=list)
    markdown_blueprint: str = Field(..., description="Renderable markdown specifications")
