# Quality Engineering Skill

## Purpose

Formulate testing strategies, test plans, and verification matrices to verify system correctness and performance under load.

## Responsibilities

- Define unit test suites (Jest/Pytest)
- Plan integration and E2E tests (Playwright)
- Define performance and stress load testing targets (k6)
- Detail edge cases and negative validation inputs

## Inputs

- Requirements Specification
- OpenAPI Contract

## Outputs

- Verification Matrix / Test Plan
- Automation Script / Mock layout definitions

## Review Criteria

- Code coverage metrics
- Concurrency and load limits checked
- Reliability and idempotency of tests
- Boundary and validation checking

## Guardrails

- Always include performance load test specifications.
- Never omit negative or edge case validations (invalid input, unauthorized access).
