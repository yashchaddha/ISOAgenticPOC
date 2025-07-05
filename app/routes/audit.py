# app/routes/audit.py

from typing import Optional
from fastapi import APIRouter, HTTPException

from app.models.audit import (
    StartAuditResponse,
    QuestionResponse,
    AnswerRequest,
    QueryRequest,
    QueryResponse
)
from app.services.audit_engine import AuditEngine

router = APIRouter(prefix="/audit", tags=["audit"])

@router.post("/start", response_model=StartAuditResponse)
async def start_audit():
    session_id = await AuditEngine.create_session()
    return StartAuditResponse(session_id=session_id)

@router.get("/{session_id}/next", response_model=Optional[QuestionResponse])
async def get_next_clause(session_id: str):
    try:
        meta = await AuditEngine.next_clause(session_id)
    except KeyError:
        raise HTTPException(404, "Session not found")

    if meta is None:
        # audit complete
        return None

    return QuestionResponse(
        question=meta["question"],
        description=meta["description"],
        attributes=meta["attributes"],
    )

@router.post("/{session_id}/query", response_model=QueryResponse)
async def query_clause(session_id: str, req: QueryRequest):
    try:
        resp = await AuditEngine.handle_query(session_id, req.query)
    except KeyError:
        raise HTTPException(404, "Session not found")
    return QueryResponse(response=resp)

@router.post("/{session_id}/answer", status_code=204)
async def post_answer(session_id: str, req: AnswerRequest):
    try:
        await AuditEngine.record_answer(session_id, req.answer)
    except KeyError:
        raise HTTPException(404, "Session not found")
    except IndexError:
        raise HTTPException(400, "No more clauses to answer")
