# Agent Design

## Execution Order

User Idea
→ Project Manager Agent
→ Requirements Agent
→ Architecture Agent
→ Database Agent
→ API Agent
→ Testing Agent
→ Risk Reviewer Agent
→ Documentation Agent
→ Final Package

## Agents

### 1. Project Manager Agent
Input: rough project idea  
Output: clarified project brief  
Skill: project-manager  
Guardrail: must not generate code; must clarify unclear scope.

### 2. Requirements Agent
Input: clarified brief  
Output: functional and non-functional requirements  
Skill: requirements-writer  
Guardrail: must include assumptions and out-of-scope items.

### 3. Architecture Agent
Input: requirements  
Output: system architecture  
Skill: software-architect  
Guardrail: must explain trade-offs.

### 4. Database Agent
Input: requirements + architecture  
Output: database entities and relationships  
Skill: data-modeler  
Guardrail: must flag sensitive data.

### 5. API Agent
Input: requirements + data model  
Output: API contract  
Skill: api-designer  
Guardrail: must avoid exposing secrets or unsafe endpoints.

### 6. Testing Agent
Input: all generated specs  
Output: unit, integration, E2E, and security test plan  
Skill: test-planner  
Guardrail: must include negative and edge cases.

### 7. Risk Reviewer Agent
Input: full generated package  
Output: risk review and score  
Skill: risk-reviewer  
Guardrail: must flag missing security, privacy, deployment, or testing controls.

### 8. Documentation Agent
Input: reviewed package  
Output: final readable delivery pack  
Skill: documentation-writer  
Guardrail: must preserve traceability from idea to output.
