import os
from typing import Dict, Any, List
from app.services.llm_service import generate_with_llm

# Specialist Agent definitions, mapping IDs to metadata, personas, and prompts.
# Design decision: Each specialist has a clear system role, set of duties, and structured templates.
SPECIALISTS: Dict[str, Dict[str, Any]] = {
    "coordination": {
        "discipline_name": "Engineering Coordinator",
        "role": "Orchestrates specifications alignment & schedules workloads",
        "avatar": "Engineering Coordinator",
        "confidence": 100,
        "active_tab": "summary"
    },
    "requirements": {
        "discipline_name": "Requirements Engineering",
        "role": "Formalizes functional specifications & scalability boundaries",
        "avatar": "Requirements Engineering",
        "confidence": 96,
        "active_tab": "requirements"
    },
    "architecture": {
        "discipline_name": "Architecture Engineering",
        "role": "Models component systems topology & integration layers",
        "avatar": "Architecture Engineering",
        "confidence": 92,
        "active_tab": "architecture"
    },
    "database": {
        "discipline_name": "Data Engineering",
        "role": "Designs relational entities, constraints & indexing rules",
        "avatar": "Data Engineering",
        "confidence": 95,
        "active_tab": "database"
    },
    "api": {
        "discipline_name": "Integration Engineering",
        "role": "Maps HTTP routes, payloads & service interfaces",
        "avatar": "Integration Engineering",
        "confidence": 94,
        "active_tab": "api"
    },
    "testing": {
        "discipline_name": "Quality Engineering",
        "role": "Establishes testing harness matrices (Jest, Playwright, k6)",
        "avatar": "Quality Engineering",
        "confidence": 93,
        "active_tab": "testing"
    },
    "risk": {
        "discipline_name": "Risk Engineering",
        "role": "Audits compliance, security mitigations & rate throttling",
        "avatar": "Risk Engineering",
        "confidence": 88,
        "active_tab": "risks"
    },
    "architecture_retry": {
        "discipline_name": "Architecture Engineering (Revision)",
        "role": "Models component systems topology & integration layers",
        "avatar": "Architecture Engineering",
        "confidence": 96,
        "active_tab": "architecture"
    },
    "risk_retry": {
        "discipline_name": "Risk Engineering (Re-evaluation)",
        "role": "Audits compliance, security mitigations & rate throttling",
        "avatar": "Risk Engineering",
        "confidence": 97,
        "active_tab": "risks"
    },
    "communication": {
        "discipline_name": "Technical Communication",
        "role": "Compiles unified engineering blueprint package documentation",
        "avatar": "Technical Communication",
        "confidence": 99,
        "active_tab": "summary"
    }
}


def get_specialist_dialogue(step_id: str, idea: str) -> List[Dict[str, str]]:
    """
    Returns dialogue text matching the specialist's analysis of the idea.
    """
    spec = SPECIALISTS.get(step_id, SPECIALISTS["coordination"])
    author = spec["avatar"]
    
    dialogues = {
        "coordination": f"Welcome to the engineering session. I have mapped out our target architecture for '{idea}'. Initiating specialists...",
        "requirements": f"The current requirements do not define expected concurrent users for '{idea}'. I'll assume a two-user system and flag this assumption for review.",
        "architecture": "Based on requirements, I'm proposing a Modular Monolith pattern. It satisfies latency targets and reduces operational overhead. Authentication is modeled as a simple session handler for now.",
        "database": "I've structured the SQL relational layout. Primary keys are UUIDs. Audit fields (`created_at`, `updated_at`) are appended to all tables. Let's make sure password hashing doesn't leak credentials.",
        "api": f"I've mapped out the API endpoints for '{idea}'. Exposed REST schemas handle user state and workspace updates. No rate limiting has been specified yet.",
        "testing": "The architecture is stable enough to begin test planning. I'll prepare functional, integration, performance, and security test scenarios.",
        "risk": "Critical audit failure. The authentication flow lacks rate limiting, OAuth2 security specifications, and token rotation rules. Reopening Architecture Review immediately.",
        "architecture_retry": "Feedback received. I am updating the system architecture. We have added an API Gateway proxy layer executing rate limiting (Token Bucket) and standard OAuth2 authentication with JWT token rotation.",
        "risk_retry": "Re-evaluation completed. The revised architecture successfully mitigates the rate-limiting and OAuth2 security vulnerabilities. Readiness score promoted to 94/100.",
        "communication": f"I have compiled the final Engineering Blueprint package for '{idea}'. The specification package is fully aligned, review-approved, and ready for developer handoff."
    }
    
    msg = dialogues.get(step_id, dialogues["coordination"])
    return [{"author": author, "message": msg}]


def get_skill_content(filename: str) -> str:
    """Reads the contents of the specified skill file from the backend/app/skills/ folder."""
    try:
        skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
        filepath = os.path.join(skills_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return f.read().strip()
    except Exception as e:
        print(f"Warning: Failed to load skill file {filename}: {e}")
    return ""


def generate_specialist_blueprint(step_id: str, idea: str) -> str:
    """
    Coordinates prompt generation logic and calls Gemini (with predefined fallbacks) 
    to obtain a customized specification output.
    """
    spec = SPECIALISTS.get(step_id, SPECIALISTS["coordination"])
    
    prompts = {
        "coordination": f"Generate a short executive summary in markdown for starting an engineering session for this project idea: '{idea}'. Keep it under 150 words.",
        "requirements": f"Generate a clear markdown specifications document listing 3 functional requirements (FR-1, FR-2, FR-3) and 2 non-functional requirements (NFR-1, NFR-2) tailored to this product: '{idea}'. Do not include code.",
        "architecture": f"Generate a system architecture design in markdown for '{idea}'. Suggest a Modular Monolith pattern and describe components. Mention a simple authentication helper placeholder.",
        "database": f"Generate PostgreSQL DDL schemas or markdown tables showing entity fields for users, settings, and main structures for '{idea}'. Make it look professional.",
        "api": f"Generate OpenAPI 3.0 yaml routes for user login and core resource creation for '{idea}'. Output as YAML inside markdown block.",
        "testing": f"Generate a test plan in markdown describing unit, integration, and performance E2E testing for '{idea}'.",
        "risk": f"Generate a security audit risk review in markdown for '{idea}' highlighting insecure simple authentication and lack of rate limiting. Highlight the risk clearly.",
        "architecture_retry": f"Generate a revised system architecture design in markdown for '{idea}'. Integrate OAuth2, JWT, rate-limiting, and state how it patches the security vulnerability.",
        "risk_retry": f"Generate a successful security audit review in markdown for '{idea}' after rate limiting and OAuth2 were implemented. State that it is ready for human review.",
        "communication": f"Generate a final executive summary and file checklist in markdown for this idea: '{idea}'. Make it look clean and highly professional."
    }
    
    fallbacks = {
        "coordination": f"# Executive Summary\n\n**Project Idea:** {idea}\n\n**Goal:** Formulate a production-ready engineering blueprint. We have initialized the collaborative workflow and routed parameters to the relevant engineering disciplines.",
        "requirements": f"# Requirements Specification\n\n## Functional Requirements\n- **FR-1 Scope Initialization:** Users can instantiate the workspace for the application.\n- **FR-2 Collaboration Core:** Real-time state syncing and user interactions for '{idea}' are broadcast.\n- **FR-3 Export State:** Blueprints can be exported to standard formats.\n\n## Non-Functional Requirements\n- **NFR-1 Latency:** State sync checks completed under 100ms.\n- **NFR-2 High Availability:** Target SLA of 99.9% uptime.",
        "architecture": f"# System Architecture\n\n## Monolithic Topology\n- **API Router:** Receives incoming client HTTP/WebSocket payloads.\n- **Core Engine:** Handles logic processes for '{idea}'.\n- **In-Memory Cache:** Fast key-value storage layer.\n\n## Security Note\n- *Draft auth flow placeholder implemented.*",
        "database": f"# Database Design\n\n## Relational Schema\n\n### User Table\n- `id` UUID (Primary Key)\n- `email` VARCHAR(255)\n- `password_hash` VARCHAR(512)\n\n### Main Entity Table\n- `id` UUID (Primary Key)\n- `creator_id` UUID (Foreign Key -> User.id)\n- `data_payload` JSONB\n- `updated_at` TIMESTAMP",
        "api": f"# API Contract\n\n```yaml\nopenapi: 3.0.0\ninfo:\n  title: {idea} API\n  version: 1.0.0\npaths:\n  /auth/login:\n    post:\n      summary: Authenticate user\n  /workspace:\n    post:\n      summary: Create new workspace\n```",
        "testing": f"# Verification Matrix\n\n## Test Suites\n- **Unit Tests:** Jest assertion coverage target > 90%.\n- **Integration Tests:** Playwright UI test simulation.\n- **Load Tests:** k6 WebSocket load test representing 1500 parallel users.",
        "risk": f"# Risk & Security Audit\n\n## Audit Finding\n- **Risk Status:** FAILED\n- **Critical Risk:** The authentication system has no security controls. Rate-limiting is missing on public routes, creating DDoS vulnerabilities.\n\n## Action Required\n- Revise architecture design to incorporate JWT token rotation and API gateway throttling.",
        "architecture_retry": f"# System Architecture (REVISED)\n\n## Monolithic Security Enhancement\n- **API Gateway Layer:** Added rate-limiting (Token Bucket throttling) on all client endpoints.\n- **Authentication Provider:** Integrated OAuth2 with JWT token rotation.\n- **Engine Core:** Session checking enforces secure payload validation.",
        "risk_retry": f"# Risk & Security Audit (PASSED)\n\n## Audit Finding\n- **Risk Status:** PASSED\n- **Mitigations Verified:** Throttling policies, rate limiting, and OAuth2 security are successfully integrated.\n\n## Final Evaluation\n- The engineering blueprint is verified and ready for developers.",
        "communication": f"# Engineering Blueprint Package\n\n## Package Contents\n1. **Requirements Specification** - Verified scope boundaries\n2. **System Architecture** - Revised with OAuth2 and rate-limiting\n3. **Database Schema** - Relational PostgreSQL mapping\n4. **API Specification** - OpenAPI schema\n5. **Verification Matrix** - Jest & k6 configurations\n6. **Risk Audit Report** - Passed security standards"
    }

    # Map step_id to its corresponding skill file name
    skill_file_map = {
        "coordination": "engineering_coordinator.md",
        "requirements": "requirements_engineering.md",
        "architecture": "architecture_engineering.md",
        "database": "data_engineering.md",
        "api": "integration_engineering.md",
        "testing": "quality_engineering.md",
        "risk": "risk_engineering.md",
        "architecture_retry": "architecture_engineering.md",
        "risk_retry": "risk_engineering.md",
        "communication": "technical_communication.md",
    }
    
    skill_file = skill_file_map.get(step_id, "engineering_coordinator.md")
    skill_content = get_skill_content(skill_file)
    
    prompt = prompts.get(step_id, prompts["coordination"])
    fallback = fallbacks.get(step_id, fallbacks["coordination"])
    
    # Prepend the skill content (purpose, responsibilities, review criteria, guardrails)
    # directly into the prompt so the LLM is constrained by the exact behavioral contract.
    if skill_content:
        prompt = f"Behavioral Contract:\n{skill_content}\n\nTask instructions:\n{prompt}"
        
    return generate_with_llm(prompt, fallback)
