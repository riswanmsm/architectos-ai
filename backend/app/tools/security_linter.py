"""
Security Linter Tool for Risk Engineering Specialist.
Adversarial SAST and security architecture scanner for pre-flight spec auditing.
"""
import re
from typing import Dict, Any, List


class SecurityLinter:
    """
    Adversarial security scanner.
    Analyzes architecture and API contracts for vulnerabilities, unauthenticated routes, and missing guardrails.
    """

    @classmethod
    def lint_system(cls, architecture_text: str, api_text: str, ddl_text: str, test_text: str) -> Dict[str, Any]:
        critical_findings: List[Dict[str, str]] = []
        high_findings: List[Dict[str, str]] = []
        passed_rules: List[str] = []

        combined = f"{architecture_text}\n{api_text}\n{ddl_text}\n{test_text}"

        # 1. Rate Limiting / DoS Protection Check
        has_rate_limiting = bool(re.search(
            r"\b(rate-limit|rate\s+limiting|throttling|token\s+bucket|leaky\s+bucket|api\s+gateway\s+throttl)\b",
            combined,
            re.IGNORECASE
        ))
        if not has_rate_limiting:
            critical_findings.append({
                "rule_id": "SEC-01",
                "severity": "CRITICAL",
                "message": "Missing API Gateway rate-limiting / DDoS throttling controls on client-facing routes.",
                "remediation": "Inject Token Bucket rate-limiting policy at the API Gateway proxy layer."
            })
        else:
            passed_rules.append("SEC-01: Rate Limiting & Throttling Controls Verified")

        # 2. Insecure Auth Placeholder Check
        has_auth_placeholder = bool(re.search(
            r"\b(placeholder auth|simple session handler|draft auth flow|insecure auth)\b",
            architecture_text,
            re.IGNORECASE
        ))
        has_production_auth = bool(re.search(
            r"\b(OAuth2|JWT|token\s+rotation|bearer\s+token|OIDC)\b",
            combined,
            re.IGNORECASE
        ))

        if has_auth_placeholder or not has_production_auth:
            critical_findings.append({
                "rule_id": "SEC-02",
                "severity": "CRITICAL",
                "message": "Insecure or placeholder authentication mechanism detected in architecture.",
                "remediation": "Upgrade authentication layer to OAuth2 with JWT access and refresh token rotation."
            })
        else:
            passed_rules.append("SEC-02: Hardened OAuth2/JWT Authentication Verified")

        # 3. Negative Security Testing Check
        has_negative_tests = bool(re.search(
            r"\b(negative|unauthorized|401|403|429|token\s+rejection|tamper|invalid\s+token)\b",
            test_text,
            re.IGNORECASE
        ))
        if not has_negative_tests:
            high_findings.append({
                "rule_id": "SEC-03",
                "severity": "HIGH",
                "message": "Test plan lacks negative security assertions (401/403 rejection, 429 rate limit violation).",
                "remediation": "Add explicit negative security test cases verifying invalid token and unauthorized path rejections."
            })
        else:
            passed_rules.append("SEC-03: Negative Security Test Assertions Verified")

        # 4. Credential Storage Check
        has_plaintext_creds = bool(re.search(
            r"\b(password\s+varchar|secret\s+varchar)\b",
            ddl_text,
            re.IGNORECASE
        )) and not bool(re.search(r"password_hash|secret_hash", ddl_text, re.IGNORECASE))

        if has_plaintext_creds:
            critical_findings.append({
                "rule_id": "SEC-04",
                "severity": "CRITICAL",
                "message": "Database schema defines plaintext password/secret column without cryptographic hashing.",
                "remediation": "Ensure password fields use 'password_hash' with bcrypt/argon2 hashing."
            })
        else:
            passed_rules.append("SEC-04: Secure Password Hashing Storage Verified")

        is_passed = len(critical_findings) == 0
        total_rules = len(critical_findings) + len(high_findings) + len(passed_rules)
        score = round((len(passed_rules) / total_rules) * 100, 1) if total_rules > 0 else 100.0

        return {
            "audit_passed": is_passed,
            "security_score": score,
            "critical_findings": critical_findings,
            "high_findings": high_findings,
            "passed_rules": passed_rules
        }
