# MCP Design

ArchitectOS AI uses a local MCP server as a reusable software engineering knowledge source.

## MCP Tools

### get_architecture_patterns
Returns recommended architecture patterns such as monolith, modular monolith, microservices, event-driven, and serverless.

### get_security_checklist
Returns security checks including authentication, authorization, secrets, input validation, logging, and PII handling.

### get_api_guidelines
Returns REST API design rules, naming conventions, status codes, pagination, and error response standards.

### get_database_patterns
Returns guidance for relational schema design, audit fields, soft delete, indexing, and sensitive data handling.

### get_testing_checklist
Returns unit, integration, E2E, regression, security, and acceptance testing guidance.

## Purpose

The MCP server prevents each agent from relying only on generic model knowledge. It gives agents a controlled and reusable engineering knowledge layer.
