from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import ProjectIdea, StepRequest, HumanApprovalRequest
from app.orchestrator.coordinator import (
    start_session_instance,
    execute_step_instance,
    record_human_approval,
    export_session_trajectory,
    sessions,
)
from app.orchestrator.kiro_exporter import (
    format_kiro_specs,
    create_kiro_zip_archive,
)
from app.mcp.server import mcp_router

# FastAPI App setup
app = FastAPI(
    title="ArchitectOS Engineering Coordinator & MCP Server API",
    description="Orchestrates engineering workflow pipelines, deterministic cross-artifact verification, human review gates, and .kiro/specs/ export.",
    version="1.0.0"
)

# Enable Cross-Origin Resource Sharing (CORS) for local frontend queries
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Model Context Protocol (MCP) router for Kiro and IDE integrations
app.include_router(mcp_router)


@app.get("/")
def health_check():
    """
    Health check status endpoint.
    Used for docker validation and continuous integration checks.
    """
    return {
        "status": "ok", 
        "service": "ArchitectOS Coordinator Engine",
        "version": "1.0.0",
        "mcp_enabled": True
    }


@app.post("/api/session/start")
def start_session(payload: ProjectIdea):
    """
    Entrypoint to start a new collaborative design session.
    Initializes session history, artifacts store, and trajectory tracker.
    """
    return start_session_instance(payload.idea)


@app.post("/api/session/step")
def execute_step(req: StepRequest):
    """
    Executes a single step in the engineering workflow pipeline.
    Invokes the target specialist discipline, shares upstream context,
    runs deterministic verification, and performs iterative self-correction.
    """
    return execute_step_instance(req)


@app.post("/api/session/approval")
def submit_human_approval(payload: HumanApprovalRequest):
    """
    Records human architect checkpoint approval or rejection (Ground Rules 04 & 05).
    """
    return record_human_approval(payload.session_id, payload.approved, payload.notes)


@app.get("/api/session/{session_id}/trajectory")
def get_trajectory(session_id: str):
    """
    Fetches full agent execution trajectory logs for auditability (Deliverable 04).
    """
    return export_session_trajectory(session_id)


@app.get("/api/session/{session_id}/export/kiro")
def export_kiro_bundle(session_id: str):
    """
    Exports the verified session blueprint formatted directly for .kiro/specs/.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    session = sessions[session_id]
    specs = format_kiro_specs(session.get("artifacts", {}), session.get("verifier_result"))
    return {
        "session_id": session_id,
        "idea": session.get("idea"),
        "kiro_specs": specs
    }


@app.get("/api/session/{session_id}/export/kiro/zip")
def download_kiro_zip(session_id: str):
    """
    Downloads a ready-to-unzip .kiro/specs/ archive for direct placement into any repository root.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    session = sessions[session_id]
    specs = format_kiro_specs(session.get("artifacts", {}), session.get("verifier_result"))
    zip_buffer = create_kiro_zip_archive(specs)
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=architectos-kiro-specs-{session_id[:8]}.zip"}
    )
