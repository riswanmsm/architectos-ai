# ArchitectOS AI - Architecture

## Vision
ArchitectOS AI is a multi-agent software delivery assistant that converts a rough business idea into a structured production-ready specification package.

## Primary User
Product managers, founders, software engineers, and technical leads who need to turn unclear ideas into clear delivery plans.

## Core Workflow
1. User enters a rough project idea.
2. Project Manager Agent asks clarifying questions.
3. Requirements Agent generates functional and non-functional requirements.
4. Architecture Agent creates system architecture.
5. API Agent designs API contracts.
6. Database Agent designs data model.
7. Testing Agent creates test plan.
8. Risk Reviewer Agent checks security, feasibility, and missing areas.
9. Final output is exported into a `/specs` package.

## Agents
- Project Manager Agent
- Requirements Agent
- Architecture Agent
- API Agent
- Database Agent
- Testing Agent
- Risk Reviewer Agent
- Documentation Agent

## Course Concepts Demonstrated
- Multi-agent workflow
- Agent skills
- MCP server
- Security guardrails
- Human-in-the-loop review
- Evaluation scoring
- Spec-driven development
- Deployability

## Output Files
- requirements.md
- architecture.md
- api.yaml
- database.md
- test_plan.md
- deployment.md
- risk_review.md
- executive_summary.md

## Guardrails
- No API keys or secrets in generated output
- Warn when user asks for unsafe architecture
- Require human approval before deployment recommendations
- Include security review in every generated package
- Keep generated output explainable and auditable

## MVP Scope
The first version will run locally with a React frontend and FastAPI backend. It will use Gemini API through agent orchestration and a local MCP server for reusable engineering knowledge.
