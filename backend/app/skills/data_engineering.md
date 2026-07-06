# Data Engineering Skill

## Purpose

Design a secure, optimized relational database layout and data schema that satisfies project requirements.

## Responsibilities

- Identify database entities and relationships (ERD)
- Design normalized table structures (SQL DDL)
- Append audit fields (created_at, updated_at) to all tables
- Identify and classify sensitive fields (PII, credentials)

## Inputs

- Requirements Specification
- System Architecture Design

## Outputs

- Database Entity Schema
- Relational Table Definitions (DDL)
- Sensitive Data Classification

## Review Criteria

- Normalization and duplication reduction
- Query efficiency and indexing strategies
- Data integrity and constraint enforcement
- Security (credentials protection)

## Guardrails

- Never store passwords or tokens in plain text.
- Always use UUIDs for primary keys in distributed/web environments.
- Enforce strict foreign key constraints.
