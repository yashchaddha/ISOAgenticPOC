# app/agents/tools.py

from typing import Dict, Any, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime

from app.services.mongo_client import db
from app.services.audit_engine import CLAUSE_METADATA


class GetCurrentClauseInput(BaseModel):
    session_id: str = Field(description="The audit session ID")


class GetCurrentClauseTool(BaseTool):
    name: str = "get_current_clause"
    description: str = "Get the current ISO 27001 clause being audited"
    args_schema: type = GetCurrentClauseInput
    
    def _run(self, session_id: str) -> Dict[str, Any]:
        """Get the current clause for the session (synchronous)"""
        import asyncio
        return asyncio.run(self._arun(session_id))
    
    async def _arun(self, session_id: str) -> Dict[str, Any]:
        """Get the current clause for the session"""
        sess = await db.sessions.find_one({"_id": session_id})
        if not sess:
            return {"error": "Session not found"}
        
        idx = sess.get("clause_index", 0)
        if idx >= len(CLAUSE_METADATA):
            return {"error": "Audit complete", "clause_index": idx}
        
        return {
            "clause": CLAUSE_METADATA[idx],
            "clause_index": idx,
            "total_clauses": len(CLAUSE_METADATA)
        }


class RecordAnswerInput(BaseModel):
    session_id: str = Field(description="The audit session ID")
    answer: str = Field(description="The user's answer to the current clause")


class RecordAnswerTool(BaseTool):
    name: str = "record_answer"
    description: str = "Record the user's answer for the current clause and advance to next"
    args_schema: type = RecordAnswerInput
    
    def _run(self, session_id: str, answer: str) -> Dict[str, Any]:
        """Record answer and advance to next clause (synchronous)"""
        import asyncio
        return asyncio.run(self._arun(session_id, answer))
    
    async def _arun(self, session_id: str, answer: str) -> Dict[str, Any]:
        """Record answer and advance to next clause"""
        sess = await db.sessions.find_one({"_id": session_id})
        if not sess:
            return {"error": "Session not found"}
        
        idx = sess.get("clause_index", 0)
        if idx >= len(CLAUSE_METADATA):
            return {"error": "No more clauses to answer"}
        
        clause_text = CLAUSE_METADATA[idx]["question"]
        
        # Record the answer
        await db.responses.insert_one({
            "session_id": session_id,
            "clause_index": idx,
            "clause": clause_text,
            "answer": answer,
            "answered_at": datetime.utcnow()
        })
        
        # Advance to next clause
        await db.sessions.update_one(
            {"_id": session_id},
            {"$inc": {"clause_index": 1}}
        )
        
        return {
            "success": True,
            "recorded_clause": clause_text,
            "next_clause_index": idx + 1
        }


class AnalyzeDocumentInput(BaseModel):
    document_key: str = Field(description="The S3 key of the uploaded document")
    clause_context: str = Field(description="The current clause being audited")


class AnalyzeDocumentTool(BaseTool):
    name: str = "analyze_document"
    description: str = "Analyze uploaded documents for compliance with current clause"
    args_schema: type = AnalyzeDocumentInput
    
    def _run(self, document_key: str, clause_context: str) -> Dict[str, Any]:
        """Analyze document for compliance (synchronous)"""
        import asyncio
        return asyncio.run(self._arun(document_key, clause_context))
    
    async def _arun(self, document_key: str, clause_context: str) -> Dict[str, Any]:
        """Analyze document for compliance"""
        # This would integrate with your document analysis service
        # For now, return a placeholder analysis
        return {
            "document_key": document_key,
            "clause_context": clause_context,
            "compliance_found": True,
            "relevant_sections": ["Section 1", "Section 2"],
            "confidence_score": 0.85,
            "analysis_summary": f"Document appears to address {clause_context} requirements"
        }


class CalculateComplianceScoreInput(BaseModel):
    session_id: str = Field(description="The audit session ID")


class CalculateComplianceScoreTool(BaseTool):
    name: str = "calculate_compliance_score"
    description: str = "Calculate overall compliance score based on all answers"
    args_schema: type = CalculateComplianceScoreInput
    
    def _run(self, session_id: str) -> Dict[str, Any]:
        """Calculate compliance score (synchronous)"""
        import asyncio
        return asyncio.run(self._arun(session_id))
    
    async def _arun(self, session_id: str) -> Dict[str, Any]:
        """Calculate compliance score"""
        responses = await db.responses.find({"session_id": session_id}).to_list(length=100)
        
        if not responses:
            return {"error": "No responses found for session"}
        
        # Simple scoring logic - can be enhanced
        total_responses = len(responses)
        positive_keywords = ["yes", "implemented", "compliant", "adequate", "sufficient"]
        
        positive_count = 0
        for response in responses:
            answer_lower = response["answer"].lower()
            if any(keyword in answer_lower for keyword in positive_keywords):
                positive_count += 1
        
        compliance_score = (positive_count / total_responses) * 100 if total_responses > 0 else 0
        
        return {
            "compliance_score": compliance_score,
            "total_responses": total_responses,
            "positive_responses": positive_count,
            "assessment_date": datetime.utcnow().isoformat()
        }


class GenerateRecommendationsInput(BaseModel):
    session_id: str = Field(description="The audit session ID")
    compliance_score: float = Field(description="The calculated compliance score")


class GenerateRecommendationsTool(BaseTool):
    name: str = "generate_recommendations"
    description: str = "Generate recommendations based on audit findings and compliance score"
    args_schema: type = GenerateRecommendationsInput
    
    def _run(self, session_id: str, compliance_score: float) -> Dict[str, Any]:
        """Generate recommendations (synchronous)"""
        import asyncio
        return asyncio.run(self._arun(session_id, compliance_score))
    
    async def _arun(self, session_id: str, compliance_score: float) -> Dict[str, Any]:
        """Generate recommendations"""
        responses = await db.responses.find({"session_id": session_id}).to_list(length=100)
        
        recommendations = []
        
        if compliance_score < 70:
            recommendations.append("Implement comprehensive ISMS framework")
            recommendations.append("Conduct staff training on information security")
            recommendations.append("Establish regular security audits")
        
        if compliance_score < 50:
            recommendations.append("Prioritize critical security controls")
            recommendations.append("Engage external security consultants")
            recommendations.append("Develop incident response procedures")
        
        # Analyze specific responses for targeted recommendations
        for response in responses:
            answer_lower = response["answer"].lower()
            if "no" in answer_lower or "not implemented" in answer_lower:
                clause = response["clause"]
                recommendations.append(f"Address gaps in {clause}")
        
        return {
            "recommendations": recommendations,
            "priority_level": "high" if compliance_score < 70 else "medium" if compliance_score < 85 else "low",
            "estimated_implementation_time": "3-6 months" if compliance_score < 70 else "1-3 months"
        }


# Tool registry
AUDIT_TOOLS = [
    GetCurrentClauseTool(),
    RecordAnswerTool(),
    AnalyzeDocumentTool(),
    CalculateComplianceScoreTool(),
    GenerateRecommendationsTool()
] 