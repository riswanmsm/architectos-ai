from typing import Optional
from pydantic import BaseModel, Field

class ProjectIdea(BaseModel):
    """
    Schema representing the user's initial project idea input.
    Used for creating a new design session.
    """
    idea: str = Field(
        ..., 
        description="The raw description or scope overview of the application to design.",
        examples=["A real-time whiteboard app with rooms, draw history, and export functions"]
    )

class StepRequest(BaseModel):
    """
    Schema representing the execution request parameters for an individual 
    specialist engineering step in the session pipeline.
    """
    session_id: str = Field(
        ..., 
        description="The unique UUID session identifier matching the active design session."
    )
    step_id: str = Field(
        ..., 
        description="The identifier of the engineering workflow step (e.g. 'requirements', 'architecture')."
    )
    idea: str = Field(
        ..., 
        description="The project idea to guide the specialist's analysis."
    )

class HumanApprovalRequest(BaseModel):
    """
    Schema representing human architect review approval/rejection (Ground Rules 04 & 05).
    """
    session_id: str = Field(..., description="The unique session identifier.")
    approved: bool = Field(..., description="Whether the human architect approved the design.")
    notes: Optional[str] = Field(default=None, description="Optional reviewer notes or feedback.")
