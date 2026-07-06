from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import ProjectIdea, StepRequest
from app.orchestrator.coordinator import start_session_instance, execute_step_instance

# FastAPI App setup
app = FastAPI(
    title="ArchitectOS Engineering Coordinator API",
    description="Orchestrates engineering workflow pipelines and coordinates review iterations for software specifications.",
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


@app.get("/")
def health_check():
    """
    Health check status endpoint.
    Used for docker validation and continuous integration checks.
    """
    return {
        "status": "ok", 
        "service": "ArchitectOS Coordinator Engine",
        "version": "1.0.0"
    }


@app.post("/api/session/start")
def start_session(payload: ProjectIdea):
    """
    Entrypoint to start a new collaborative design session.
    Initializes session history map.
    """
    return start_session_instance(payload.idea)


@app.post("/api/session/step")
def execute_step(req: StepRequest):
    """
    Executes a single step in the engineering workflow pipeline.
    Invokes the target specialist discipline and performs iterative self-correction.
    """
    return execute_step_instance(req)
