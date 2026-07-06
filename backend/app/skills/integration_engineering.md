# Integration Engineering Skill

## Purpose

Map out web services interfaces and construct API contracts matching the database entities and functional requirements.

## Responsibilities

- Design RESTful HTTP routes and methods
- Document payload models (JSON schemas)
- Define status codes and error responses
- Standardize OpenAPI schemas

## Inputs

- Requirements Specification
- Database Entity Schema

## Outputs

- OpenAPI 3.0 Contract (YAML/JSON)
- Integration Specifications

## Review Criteria

- REST naming standards and resource conventions
- Security constraints and endpoint protection
- Consistent error payload structures
- API contract clarity

## Guardrails

- Never expose raw database keys or tables without abstraction.
- Ensure all public endpoints are fully documented.
- Include payload models for standard responses.
