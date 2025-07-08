# app/agents/state.py

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class AuditStatus(str, Enum):
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditState(BaseModel):
    """State for the ISO 27001 audit agent"""
    
    # Session management
    session_id: str
    status: AuditStatus = AuditStatus.INITIALIZED
    created_at: datetime
    updated_at: datetime
    
    # Current audit progress
    current_clause_index: int = 0
    total_clauses: int = 0
    
    # Audit data
    current_clause: Optional[Dict[str, Any]] = None
    user_answers: Dict[int, str] = {}
    audit_findings: List[Dict[str, Any]] = []
    
    # Agent context
    conversation_history: List[Dict[str, str]] = []
    current_query: Optional[str] = None
    agent_response: Optional[str] = None
    pending_answer: Optional[str] = None
    
    # Analysis results
    compliance_score: Optional[float] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    recommendations: List[str] = []
    
    # Document analysis
    uploaded_documents: List[str] = []
    document_analysis: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True


def create_initial_state(session_id: str) -> AuditState:
    """Create initial state for a new audit session"""
    now = datetime.utcnow()
    return AuditState(
        session_id=session_id,
        created_at=now,
        updated_at=now,
        total_clauses=len(CLAUSE_METADATA)  # Will be imported from audit_engine
    )


# Import clause metadata
from app.services.audit_engine import CLAUSE_METADATA 