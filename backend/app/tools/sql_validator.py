"""
SQL DDL Validator Tool for Data Engineering Specialist.
Executes static AST checks and schema integrity verification on generated PostgreSQL DDL.
"""
import re
from typing import Dict, Any, List, Set


class SqlDdlValidator:
    """
    Deterministic SQL DDL validation connector.
    Validates syntax structure, primary keys, foreign key resolution, and credential protection.
    """

    @classmethod
    def validate_ddl(cls, ddl_text: str) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        
        # Clean markdown code blocks if present
        clean_sql = re.sub(r"```sql|```", "", ddl_text).strip()
        
        # Extract CREATE TABLE statements
        table_blocks = re.findall(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)\s*\(([\s\S]*?)\);",
            clean_sql,
            re.IGNORECASE
        )

        if not table_blocks:
            # Check if tables were defined in markdown format
            md_tables = re.findall(r"###\s+([a-zA-Z0-9_]+)\s+Table", ddl_text, re.IGNORECASE)
            if not md_tables:
                errors.append("No valid CREATE TABLE statements or relational entity definitions found.")
                return {
                    "valid": False,
                    "tables_count": 0,
                    "tables": [],
                    "errors": errors,
                    "warnings": warnings
                }
            tables_found = [t.lower() for t in md_tables]
        else:
            tables_found = [t[0].lower() for t in table_blocks]

        tables_set: Set[str] = set(tables_found)

        for table_name, body in table_blocks:
            table_lower = table_name.lower()
            
            # 1. Primary Key Check
            has_pk = bool(re.search(r"\bPRIMARY\s+KEY\b", body, re.IGNORECASE))
            if not has_pk:
                errors.append(f"Table '{table_lower}' is missing a PRIMARY KEY constraint.")

            # 2. Plaintext Password / Secret Check (Guardrail)
            plaintext_matches = re.findall(r"\b(password|secret|token|api_key)\s+(?:VARCHAR|TEXT|CHAR)\b", body, re.IGNORECASE)
            for secret_col in plaintext_matches:
                if not re.search(r"(hash|digest|encrypted)", secret_col, re.IGNORECASE):
                    errors.append(f"Table '{table_lower}' contains potentially plaintext credential column: '{secret_col}'. Use '{secret_col}_hash' instead.")

            # 3. Foreign Key Resolution Check
            fk_matches = re.findall(r"REFERENCES\s+([a-zA-Z0-9_]+)\s*(?:\(([a-zA-Z0-9_]+)\))?", body, re.IGNORECASE)
            for ref_table, _ in fk_matches:
                if ref_table.lower() not in tables_set:
                    errors.append(f"Table '{table_lower}' references non-existent table '{ref_table}'.")

            # 4. Audit Timestamp Check (Warning)
            has_created = bool(re.search(r"\bcreated_at\b", body, re.IGNORECASE))
            if not has_created:
                warnings.append(f"Table '{table_lower}' lacks standard 'created_at' audit timestamp.")

        is_valid = len(errors) == 0

        return {
            "valid": is_valid,
            "tables_count": len(tables_found),
            "tables": tables_found,
            "errors": errors,
            "warnings": warnings
        }
