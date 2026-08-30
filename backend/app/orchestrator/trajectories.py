"""
Agent Trajectory Tracking and Exporter for ArchitectOS.
Captures and formats agent execution trajectories for transparent auditability (Deliverable 04).
"""
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path


class TrajectoryTracker:
    """
    Tracks step-by-step agent instructions, tool calls, verifier outputs,
    self-correction loops, and human decisions.
    """

    def __init__(self, session_id: str, idea: str):
        self.session_id = session_id
        self.idea = idea
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.steps: List[Dict[str, Any]] = []
        self.human_checkpoints: List[Dict[str, Any]] = []

    def record_step(
        self,
        step_id: str,
        discipline_name: str,
        role: str,
        prompt: str,
        output: str,
        dialogue: List[Dict[str, str]],
        status: str,
        confidence: int,
        readiness_score: Optional[int] = None,
        risk_details: Optional[str] = None,
        verifier_checks: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        self.steps.append({
            "step_id": step_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "discipline_name": discipline_name,
            "role": role,
            "prompt_excerpt": prompt[:300] + "..." if len(prompt) > 300 else prompt,
            "output_length_chars": len(output),
            "output_preview": output[:300] + "..." if len(output) > 300 else output,
            "dialogue": dialogue,
            "status": status,
            "confidence": confidence,
            "readiness_score": readiness_score,
            "risk_details": risk_details,
            "verifier_checks": verifier_checks or []
        })

    def record_human_checkpoint(self, action: str, details: str, approved: bool) -> None:
        self.human_checkpoints.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": details,
            "approved": approved
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "idea": self.idea,
            "created_at": self.created_at,
            "total_steps": len(self.steps),
            "human_checkpoints": self.human_checkpoints,
            "trajectory": self.steps
        }

    def export_json(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return output_path
