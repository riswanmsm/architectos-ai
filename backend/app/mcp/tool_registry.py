"""
Model Context Protocol (MCP) Tool Registry for ArchitectOS.
Defines schemas and callable interfaces for integration into Kiro, Claude Desktop, Cursor, and IDEs.
"""
from typing import Dict, Any, List

MCP_TOOLS = [
    {
        "name": "architectos_generate_blueprint",
        "description": "Orchestrates an 8-specialist AI committee to generate a complete, cross-verified software architecture blueprint formatted for .kiro/specs/.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "idea": {
                    "type": "string",
                    "description": "High-level description of the software application, feature, or service to architect."
                }
            },
            "required": ["idea"]
        }
    },
    {
        "name": "architectos_verify_spec",
        "description": "Runs deterministic cross-artifact consistency checks (VBC-01 to VBC-08) across requirements, architecture, SQL schema, and API contracts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirements": {"type": "string", "description": "Markdown text containing FR-X and NFR-X specifications."},
                "architecture": {"type": "string", "description": "System architecture topology and component definitions."},
                "database": {"type": "string", "description": "PostgreSQL DDL schema or entity definitions."},
                "api": {"type": "string", "description": "OpenAPI 3.0 YAML or REST routes."},
                "testing": {"type": "string", "description": "Test matrices, unit/e2e specs, and negative test assertions."}
            },
            "required": ["requirements", "architecture"]
        }
    },
    {
        "name": "architectos_audit_risk",
        "description": "Pre-flight security and compliance gate for Spec-Driven Development (SDD). Flags missing authentication, unthrottled endpoints, and unmapped tests before code generation begins.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "architecture_spec": {"type": "string", "description": "Architecture specification markdown."},
                "api_spec": {"type": "string", "description": "OpenAPI YAML or API route definitions."}
            },
            "required": ["architecture_spec"]
        }
    }
]