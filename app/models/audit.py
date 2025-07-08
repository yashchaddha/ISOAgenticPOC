from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class StartAuditResponse(BaseModel):
    session_id: str


class QuestionResponse(BaseModel):
    question: str
    description: str
    attributes: List[str]


class AnswerRequest(BaseModel):
    answer: str


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str


# New models for agentic functionality
class AuditStatusResponse(BaseModel):
    session_id: str
    status: str
    current_clause: Optional[Dict[str, Any]] = None
    current_clause_index: int
    total_clauses: int
    compliance_score: Optional[float] = None
    recommendations: List[str] = []
    uploaded_documents: List[str] = []


class DocumentUploadRequest(BaseModel):
    document_key: str


class DocumentUploadResponse(BaseModel):
    success: bool
    document_analysis: List[Dict[str, Any]] = []
    status: str


class AuditReportResponse(BaseModel):
    session_id: str
    compliance_score: float
    recommendations: List[str]
    user_answers: Dict[int, str]
    final_report: Optional[str] = None
    generated_at: Optional[str] = None


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: str


class ConversationHistoryResponse(BaseModel):
    session_id: str
    messages: List[ConversationMessage]

