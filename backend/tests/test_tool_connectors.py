import unittest
from app.tools.sql_validator import SqlDdlValidator
from app.tools.openapi_validator import OpenApiValidator
from app.tools.security_linter import SecurityLinter


class ToolConnectorsTests(unittest.TestCase):
    def test_sql_validator_catches_missing_pk_and_broken_fk(self):
        # Broken DDL: table2 has no PK, references non-existent table3, and has plaintext password
        bad_ddl = """
        CREATE TABLE table1 (
            id UUID PRIMARY KEY,
            password VARCHAR(255)
        );
        CREATE TABLE table2 (
            user_id UUID REFERENCES table3(id)
        );
        """
        res = SqlDdlValidator.validate_ddl(bad_ddl)
        self.assertFalse(res["valid"])
        self.assertTrue(any("PRIMARY KEY" in err for err in res["errors"]))
        self.assertTrue(any("non-existent table 'table3'" in err for err in res["errors"]))
        self.assertTrue(any("plaintext" in err for err in res["errors"]))

    def test_sql_validator_passes_clean_ddl(self):
        clean_ddl = """
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(512) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        CREATE TABLE workspaces (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            creator_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        res = SqlDdlValidator.validate_ddl(clean_ddl)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)
        self.assertEqual(res["tables_count"], 2)

    def test_openapi_validator_catches_unauthenticated_mutations(self):
        bad_api = """
        openapi: 3.0.0
        paths:
          /api/v1/workspaces:
            post:
              summary: Create workspace
        """
        res = OpenApiValidator.validate_contract(bad_api)
        self.assertFalse(res["valid"])
        self.assertTrue(any("lacks any securitySchemes" in err for err in res["errors"]))

    def test_openapi_validator_passes_secure_contract(self):
        good_api = """
        openapi: 3.0.0
        paths:
          /api/v1/auth/login:
            post:
              summary: Login
          /api/v1/workspaces:
            post:
              summary: Create workspace
              security:
                - OAuth2Bearer: []
        """
        res = OpenApiValidator.validate_contract(good_api)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)

    def test_security_linter_audits_vulnerabilities(self):
        # Insecure system
        arch_bad = "Modular Monolith with draft auth flow placeholder and no rate-limiting."
        api_bad = "/login: post"
        ddl_bad = "CREATE TABLE users (id UUID, password VARCHAR(255));"
        test_bad = "Unit test."
        
        res_bad = SecurityLinter.lint_system(arch_bad, api_bad, ddl_bad, test_bad)
        self.assertFalse(res_bad["audit_passed"])
        self.assertTrue(any(f["rule_id"] == "SEC-01" for f in res_bad["critical_findings"]))
        self.assertTrue(any(f["rule_id"] == "SEC-02" for f in res_bad["critical_findings"]))

        # Hardened system
        arch_good = "Modular Monolith with API Gateway Token Bucket rate-limiting and OAuth2 JWT authentication."
        api_good = "/api/v1/workspaces: post with security OAuth2Bearer"
        ddl_good = "CREATE TABLE users (id UUID PRIMARY KEY, password_hash VARCHAR(512));"
        test_good = "TEST-1 unit, TEST-2 negative 401/403 unauthorized token rejection."

        res_good = SecurityLinter.lint_system(arch_good, api_good, ddl_good, test_good)
        self.assertTrue(res_good["audit_passed"])
        self.assertEqual(len(res_good["critical_findings"]), 0)
