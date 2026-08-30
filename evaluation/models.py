from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class TestKind(str, Enum):
    unit = "unit"
    integration = "integration"
    e2e = "e2e"
    performance = "performance"
    security = "security"


class FunctionalRequirement(StrictModel):
    id: str = Field(pattern=r"^FR-[1-9][0-9]*$")
    statement: str = Field(min_length=10)
    acceptance_criteria: list[str] = Field(min_length=1)


class NonFunctionalRequirement(StrictModel):
    id: str = Field(pattern=r"^NFR-[1-9][0-9]*$")
    statement: str = Field(min_length=10)
    target: str = Field(min_length=3)
    verification_method: str = Field(min_length=5)


class ArchitectureComponent(StrictModel):
    id: str = Field(pattern=r"^COMP-[1-9][0-9]*$")
    name: str = Field(min_length=2)
    responsibilities: list[str] = Field(min_length=1)
    requirement_ids: list[str]
    entity_ids: list[str]


class DataEntity(StrictModel):
    id: str = Field(pattern=r"^ENT-[1-9][0-9]*$")
    name: str = Field(min_length=2)
    purpose: str = Field(min_length=5)
    sensitive: bool


class ApiOperation(StrictModel):
    id: str = Field(pattern=r"^API-[1-9][0-9]*$")
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str = Field(pattern=r"^/")
    purpose: str = Field(min_length=5)
    public: bool
    authentication: str | None
    authorization: str | None
    requirement_ids: list[str]
    entity_ids: list[str]


class BlueprintTest(StrictModel):
    id: str = Field(pattern=r"^TEST-[1-9][0-9]*$")
    kind: TestKind
    description: str = Field(min_length=10)
    requirement_ids: list[str]
    api_operation_ids: list[str]
    negative: bool


class ObligationCoverage(StrictModel):
    obligation_id: str = Field(min_length=3)
    design_response: str = Field(min_length=10)
    evidence_ids: list[str] = Field(min_length=1)


class Assumption(StrictModel):
    id: str = Field(pattern=r"^ASM-[1-9][0-9]*$")
    statement: str = Field(min_length=10)
    needs_human_review: bool


class Blueprint(StrictModel):
    idea_summary: str = Field(min_length=20)
    functional_requirements: list[FunctionalRequirement] = Field(min_length=1)
    non_functional_requirements: list[NonFunctionalRequirement] = Field(min_length=1)
    architecture_components: list[ArchitectureComponent] = Field(min_length=1)
    data_entities: list[DataEntity] = Field(min_length=1)
    api_operations: list[ApiOperation] = Field(min_length=1)
    tests: list[BlueprintTest] = Field(min_length=1)
    obligation_coverage: list[ObligationCoverage]
    assumptions: list[Assumption]


class EvaluationCase(StrictModel):
    id: str = Field(pattern=r"^CASE-[0-9]{2}$")
    title: str
    idea: str
    obligations: list[str] = Field(min_length=1)
    challenging: bool = False


class CaseSet(StrictModel):
    evaluation_version: str
    frozen: bool
    primary_metric: str
    cases: list[EvaluationCase] = Field(min_length=1)
