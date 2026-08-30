from dataclasses import asdict, dataclass
import re
from typing import Iterable

from evaluation.models import Blueprint, EvaluationCase


SCORER_VERSION = "1.0.1"


@dataclass(frozen=True)
class CheckResult:
    rule_id: str
    subject_id: str
    passed: bool
    evidence: str
    critical: bool = False


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _measurable_nfr(target: str, verification_method: str) -> bool:
    objective_target = bool(
        re.search(r"\d", target)
        or re.search(r"\b(zero|none|all|every|never|no)\b", target, re.IGNORECASE)
    )
    explicit_verification = bool(re.search(
        r"\b(test|measure|inspect|audit|monitor|benchmark|scan|simulate|verify)\w*\b",
        verification_method,
        re.IGNORECASE,
    ))
    return objective_target and explicit_verification


def score_blueprint(blueprint: Blueprint, case: EvaluationCase) -> dict:
    checks: list[CheckResult] = []

    requirements = {item.id for item in blueprint.functional_requirements}
    nfrs = {item.id for item in blueprint.non_functional_requirements}
    all_requirements = requirements | nfrs
    components = {item.id for item in blueprint.architecture_components}
    entities = {item.id for item in blueprint.data_entities}
    operations = {item.id for item in blueprint.api_operations}
    tests = {item.id for item in blueprint.tests}
    evidence_ids = requirements | nfrs | components | entities | operations | tests

    for requirement_id in sorted(requirements):
        implementers = [
            item.id
            for item in blueprint.architecture_components
            if requirement_id in item.requirement_ids
        ] + [
            item.id
            for item in blueprint.api_operations
            if requirement_id in item.requirement_ids
        ]
        checks.append(CheckResult(
            "VBC-01",
            requirement_id,
            bool(implementers),
            f"implementation links: {', '.join(implementers) or 'none'}",
        ))

        covering_tests = [
            item.id for item in blueprint.tests if requirement_id in item.requirement_ids
        ]
        checks.append(CheckResult(
            "VBC-02",
            requirement_id,
            bool(covering_tests),
            f"test links: {', '.join(covering_tests) or 'none'}",
        ))

    for operation in blueprint.api_operations:
        if operation.public:
            continue
        secure = bool(operation.authentication and operation.authorization)
        checks.append(CheckResult(
            "VBC-03",
            operation.id,
            secure,
            "authentication and authorization declared" if secure else "missing authentication or authorization",
            critical=not secure,
        ))

    entity_references: list[tuple[str, str]] = []
    for component in blueprint.architecture_components:
        entity_references.extend((component.id, entity_id) for entity_id in component.entity_ids)
    for operation in blueprint.api_operations:
        entity_references.extend((operation.id, entity_id) for entity_id in operation.entity_ids)
    if not entity_references:
        checks.append(CheckResult("VBC-04", "blueprint", False, "no entity references declared"))
    for owner_id, entity_id in entity_references:
        checks.append(CheckResult(
            "VBC-04",
            f"{owner_id}->{entity_id}",
            entity_id in entities,
            "entity reference resolves" if entity_id in entities else "unknown entity reference",
        ))

    for nfr in blueprint.non_functional_requirements:
        measurable = _measurable_nfr(nfr.target, nfr.verification_method)
        checks.append(CheckResult(
            "VBC-05",
            nfr.id,
            measurable,
            "objective target and explicit verification method declared" if measurable else "target is not objective or verification method is not explicit",
        ))

    reference_groups: list[tuple[str, str, set[str]]] = []
    for component in blueprint.architecture_components:
        reference_groups.extend((component.id, ref, all_requirements) for ref in component.requirement_ids)
    for operation in blueprint.api_operations:
        reference_groups.extend((operation.id, ref, all_requirements) for ref in operation.requirement_ids)
    for test in blueprint.tests:
        reference_groups.extend((test.id, ref, all_requirements) for ref in test.requirement_ids)
        reference_groups.extend((test.id, ref, operations) for ref in test.api_operation_ids)
    if not reference_groups:
        checks.append(CheckResult("VBC-06", "blueprint", False, "no cross-artifact references declared"))
    for owner_id, reference_id, valid_ids in reference_groups:
        checks.append(CheckResult(
            "VBC-06",
            f"{owner_id}->{reference_id}",
            reference_id in valid_ids,
            "reference resolves" if reference_id in valid_ids else "unknown reference",
        ))

    protected_operations = {item.id for item in blueprint.api_operations if not item.public}
    negative_security_tests = [
        item.id
        for item in blueprint.tests
        if item.negative
        and (item.kind.value == "security" or protected_operations.intersection(item.api_operation_ids))
    ]
    checks.append(CheckResult(
        "VBC-07",
        "negative-security-coverage",
        not protected_operations or bool(negative_security_tests),
        f"negative security tests: {', '.join(negative_security_tests) or 'none'}",
    ))

    coverage_by_obligation = {
        item.obligation_id: item for item in blueprint.obligation_coverage
    }
    for obligation_id in case.obligations:
        coverage = coverage_by_obligation.get(obligation_id)
        linked_ids = coverage.evidence_ids if coverage else []
        valid_links = bool(linked_ids) and all(item in evidence_ids for item in linked_ids)
        has_design_evidence = any(
            item.startswith(("FR-", "NFR-", "COMP-", "ENT-", "API-"))
            for item in linked_ids
        )
        has_test_evidence = any(item.startswith("TEST-") for item in linked_ids)
        requires_test = obligation_id.endswith("_test") or any(
            term in obligation_id
            for term in ("idempotency", "authorization", "access", "isolation", "oversell", "double_booking")
        )
        resolved = bool(
            coverage
            and coverage.design_response.strip()
            and valid_links
            and has_design_evidence
            and (has_test_evidence or not requires_test)
        )
        critical = obligation_id in {
            "payment_idempotency",
            "billing_webhook_idempotency",
            "tenant_data_isolation",
            "tenant_and_guest_authorization",
            "room_membership_authorization",
        } and not resolved
        checks.append(CheckResult(
            "VBC-08",
            obligation_id,
            resolved,
            (
                f"evidence links: {', '.join(linked_ids)}"
                if coverage
                else "obligation not addressed"
            ),
            critical=critical,
        ))

    identifier_groups = {
        "functional_requirements": [item.id for item in blueprint.functional_requirements],
        "non_functional_requirements": [item.id for item in blueprint.non_functional_requirements],
        "architecture_components": [item.id for item in blueprint.architecture_components],
        "data_entities": [item.id for item in blueprint.data_entities],
        "api_operations": [item.id for item in blueprint.api_operations],
        "tests": [item.id for item in blueprint.tests],
    }
    duplicate_ids = sorted({
        duplicate
        for values in identifier_groups.values()
        for duplicate in _duplicates(values)
    })
    checks.append(CheckResult(
        "VBC-06",
        "unique-identifiers",
        not duplicate_ids,
        f"duplicate identifiers: {', '.join(duplicate_ids) or 'none'}",
    ))

    passed = sum(check.passed for check in checks)
    total = len(checks)
    critical_findings = [
        asdict(check) for check in checks if check.critical and not check.passed
    ]
    return {
        "scorer_version": SCORER_VERSION,
        "case_id": case.id,
        "passed_checks": passed,
        "total_checks": total,
        "verified_blueprint_coverage": round(passed / total * 100, 2) if total else 0.0,
        "ready": not critical_findings,
        "critical_findings": critical_findings,
        "checks": [asdict(check) for check in checks],
    }
