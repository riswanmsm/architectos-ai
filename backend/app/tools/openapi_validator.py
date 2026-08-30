"""
OpenAPI Validator Tool for Integration Engineering Specialist.
Validates OpenAPI 3.0 contracts, route paths, HTTP verbs, and security scheme bindings.
"""
import re
from typing import Dict, Any, List


class OpenApiValidator:
    """
    Deterministic OpenAPI 3.0 contract validator connector.
    """

    @classmethod
    def validate_contract(cls, api_text: str) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        endpoints: List[Dict[str, Any]] = []

        # Check for OpenAPI specification header
        has_openapi_header = bool(re.search(r"openapi:\s*3\.\d+\.\d+", api_text, re.IGNORECASE))
        if not has_openapi_header:
            warnings.append("API specification does not explicitly declare 'openapi: 3.0.x' version header.")

        # Extract paths
        path_matches = re.findall(r"(\s+)(/[a-zA-Z0-9_\-\/{}]*):\s*\n", api_text)
        if not path_matches:
            # Fallback markdown route search
            md_routes = re.findall(r"(?:GET|POST|PUT|PATCH|DELETE)\s+(/[a-zA-Z0-9_\-\/{}]*)", api_text)
            if not md_routes:
                errors.append("No valid API endpoints or REST route declarations found in contract.")
                return {
                    "valid": False,
                    "endpoint_count": 0,
                    "endpoints": [],
                    "errors": errors,
                    "warnings": warnings
                }
            for route in set(md_routes):
                endpoints.append({
                    "path": route,
                    "has_auth": bool(re.search(r"\b(auth|bearer|jwt|oauth2|token)\b", api_text, re.IGNORECASE))
                })
        else:
            for _, path in set(path_matches):
                if path.startswith("//"):
                    continue
                has_security = bool(re.search(
                    rf"{re.escape(path)}[\s\S]*?(?:security:\s*\n\s*-\s*|Bearer|OAuth2|JWT)",
                    api_text,
                    re.IGNORECASE
                ))
                endpoints.append({
                    "path": path,
                    "has_auth": has_security
                })

        # Check that mutation endpoints (POST/PUT/DELETE) define security or authorization
        has_mutations = bool(re.search(r"(post|put|delete|patch):", api_text, re.IGNORECASE))
        has_any_security = any(e["has_auth"] for e in endpoints) or bool(re.search(r"\b(securitySchemes|OAuth2|JWT|Bearer)\b", api_text, re.IGNORECASE))

        if has_mutations and not has_any_security:
            errors.append("API defines state-mutating endpoints (POST/PUT/DELETE) but lacks any securitySchemes or authentication headers.")

        is_valid = len(errors) == 0

        return {
            "valid": is_valid,
            "endpoint_count": len(endpoints),
            "endpoints": endpoints,
            "errors": errors,
            "warnings": warnings
        }
