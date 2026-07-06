import uuid
from typing import Dict, Any
from app.models.schemas import StepRequest
from app.agents.specialists import SPECIALISTS, get_specialist_dialogue, generate_specialist_blueprint

# In-memory session database mapping session IDs to history and metadata.
# Design decision: Simple in-memory storage for ease of local hosting and rapid iteration.
sessions: Dict[str, Dict[str, Any]] = {}


def start_session_instance(idea: str) -> Dict[str, Any]:
    """
    Initializes a new collaborative design session with a random UUID,
    and returns initial state variables.
    """
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "idea": idea,
        "history": []
    }
    return {
        "session_id": session_id,
        "status": "initialized",
        "idea": idea
    }


def execute_step_instance(req: StepRequest) -> Dict[str, Any]:
    """
    Routes a request step execution to the correct engineering discipline,
    retrieves their dialog logs, calls prompt generation, and returns status values.
    
    Includes specific audit fail/success scoring coordinates:
      - 'risk': returns score 78/100 to trigger the reopening alert
      - 'risk_retry': returns score 94/100 once revision compiles
    """
    session_id = req.session_id
    step_id = req.step_id
    idea = req.idea
    
    # Session state recovery fallback
    if session_id not in sessions:
        sessions[session_id] = {"idea": idea, "history": []}

    # Fetch specialist configuration profile
    spec = SPECIALISTS.get(step_id, SPECIALISTS["coordination"])
    discipline_name = spec["discipline_name"]
    active_tab = spec["active_tab"]
    confidence = spec["confidence"]

    # Gather dialog logs
    dialogue = get_specialist_dialogue(step_id, idea)

    # Generate document specifications
    blueprint_content = generate_specialist_blueprint(step_id, idea)

    # Readiness Score parameters
    readiness_score = None
    risk_details = None
    status = "completed"

    if step_id == "risk":
        status = "failed"
        readiness_score = 78
        risk_details = "Critical Risk: Authentication flow is incomplete. No rate-limiting or secure OAuth2 token rotation specified."
    elif step_id == "risk_retry":
        readiness_score = 94
        risk_details = "Ready for Human Review"
    elif step_id == "communication":
        readiness_score = 94
        risk_details = "Ready for Human Review"

    return {
        "discipline_name": discipline_name,
        "status": status,
        "confidence": confidence,
        "dialogue": dialogue,
        "blueprint_content": blueprint_content,
        "readiness_score": readiness_score,
        "risk_details": risk_details,
        "active_tab": active_tab
    }
