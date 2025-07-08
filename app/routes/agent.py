# app/routes/agent.py

from typing import Optional
from fastapi import APIRouter, HTTPException

from app.models.audit import (
    StartAuditResponse,
    QueryRequest,
    QueryResponse,
    AnswerRequest,
    AuditStatusResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
    AuditReportResponse,
    ConversationHistoryResponse
)
from app.agents.simple_graph import simple_audit_graph

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/start", response_model=StartAuditResponse)
async def start_agentic_audit():
    """Start a new agentic audit session"""
    try:
        session_id = await simple_audit_graph.start_audit()
        return StartAuditResponse(session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start audit: {str(e)}")


@router.post("/{session_id}/query", response_model=QueryResponse)
async def agent_query(session_id: str, req: QueryRequest):
    """Process a query through the agentic audit system"""
    try:
        result = await simple_audit_graph.process_query(session_id, req.query)
        return QueryResponse(response=result["response"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@router.post("/{session_id}/answer", status_code=200)
async def agent_answer(session_id: str, req: AnswerRequest):
    """Record an answer through the agentic audit system"""
    try:
        result = await simple_audit_graph.record_answer(session_id, req.answer)
        return {
            "success": result["success"],
            "next_clause": result["next_clause"],
            "status": result["status"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record answer: {str(e)}")


@router.get("/{session_id}/status", response_model=AuditStatusResponse)
async def get_agent_status(session_id: str):
    """Get the current status of an agentic audit session"""
    try:
        status = await simple_audit_graph.get_audit_status(session_id)
        return AuditStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/{session_id}/upload-document", response_model=DocumentUploadResponse)
async def upload_document_to_agent(session_id: str, req: DocumentUploadRequest):
    """Upload a document for analysis in the agentic audit"""
    try:
        result = await simple_audit_graph.upload_document(session_id, req.document_key)
        return DocumentUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@router.get("/{session_id}/report", response_model=AuditReportResponse)
async def get_agent_report(session_id: str):
    """Get the final audit report from the agentic system"""
    try:
        report = await simple_audit_graph.get_audit_report(session_id)
        return AuditReportResponse(**report)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.get("/{session_id}/conversation", response_model=ConversationHistoryResponse)
async def get_conversation_history(session_id: str):
    """Get the conversation history for an audit session"""
    try:
        # This would need to be implemented in the graph
        # For now, return empty conversation
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.post("/{session_id}/complete", status_code=200)
async def complete_agent_audit(session_id: str):
    """Manually complete an audit session"""
    try:
        # This would trigger the completion workflow
        # For now, just return success
        return {"success": True, "message": "Audit completion triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete audit: {str(e)}") 