# app/agents/nodes.py

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import asyncio
from datetime import datetime

from app.agents.state import AuditState, AuditStatus
from app.agents.tools import AUDIT_TOOLS
from app.services.audit_engine import CLAUSE_METADATA


class AuditNodes:
    """Nodes for the ISO 27001 audit graph"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            max_tokens=1000
        )
    
    async def initialize_session(self, state: AuditState) -> AuditState:
        """Initialize a new audit session"""
        state.status = AuditStatus.IN_PROGRESS
        state.updated_at = datetime.utcnow()
        state.current_clause_index = 0
        state.total_clauses = len(CLAUSE_METADATA)
        
        if state.current_clause_index < len(CLAUSE_METADATA):
            state.current_clause = CLAUSE_METADATA[state.current_clause_index]
        
        return state
    
    async def get_current_clause(self, state: AuditState) -> AuditState:
        """Get the current clause information"""
        if state.current_clause_index >= len(CLAUSE_METADATA):
            state.status = AuditStatus.COMPLETED
            return state
        
        state.current_clause = CLAUSE_METADATA[state.current_clause_index]
        state.updated_at = datetime.utcnow()
        
        return state
    
    async def process_user_query(self, state: AuditState) -> AuditState:
        """Process user queries about the current clause"""
        if not state.current_query or not state.current_clause:
            return state
        
        system_prompt = """You are an expert ISO 27001 internal auditor. Your role is to:
        1. Answer questions about ISO 27001 clauses clearly and accurately
        2. Provide guidance on compliance requirements
        3. Help users understand what they need to implement
        4. Be helpful but maintain professional audit standards
        
        If the query is not related to ISO 27001, politely redirect the conversation."""
        
        user_prompt = f"""
        Current Clause: {state.current_clause['question']}
        Description: {state.current_clause['description']}
        Key Attributes: {', '.join(state.current_clause['attributes'])}
        
        User Query: {state.current_query}
        
        Please provide a clear, helpful response.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        state.agent_response = response.content
        
        # Add to conversation history
        state.conversation_history.append({
            "role": "user",
            "content": state.current_query,
            "timestamp": datetime.utcnow().isoformat()
        })
        state.conversation_history.append({
            "role": "assistant", 
            "content": state.agent_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        state.updated_at = datetime.utcnow()
        return state
    
    async def record_user_answer(self, state: AuditState) -> AuditState:
        """Record the user's answer for the current clause"""
        if not state.current_clause:
            return state
        
        # This would typically come from user input
        # For now, we'll simulate it
        if hasattr(state, 'pending_answer') and state.pending_answer:
            state.user_answers[state.current_clause_index] = state.pending_answer
            
            # Add to conversation history
            state.conversation_history.append({
                "role": "user",
                "content": f"Answer for {state.current_clause['question']}: {state.pending_answer}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Clear pending answer
            state.pending_answer = None
        
        state.updated_at = datetime.utcnow()
        return state
    
    async def analyze_documents(self, state: AuditState) -> AuditState:
        """Analyze uploaded documents for compliance"""
        if not state.uploaded_documents or not state.current_clause:
            return state
        
        analysis_results = []
        for doc_key in state.uploaded_documents:
            # Use the document analysis tool
            analyze_tool = next(t for t in AUDIT_TOOLS if t.name == "analyze_document")
            result = await analyze_tool._arun(
                document_key=doc_key,
                clause_context=state.current_clause['question']
            )
            analysis_results.append(result)
        
        state.document_analysis[state.current_clause_index] = analysis_results
        state.updated_at = datetime.utcnow()
        
        return state
    
    async def advance_to_next_clause(self, state: AuditState) -> AuditState:
        """Advance to the next clause in the audit"""
        state.current_clause_index += 1
        
        if state.current_clause_index >= len(CLAUSE_METADATA):
            state.status = AuditStatus.COMPLETED
            state.current_clause = None
        else:
            state.current_clause = CLAUSE_METADATA[state.current_clause_index]
        
        state.updated_at = datetime.utcnow()
        return state
    
    async def calculate_compliance_score(self, state: AuditState) -> AuditState:
        """Calculate overall compliance score"""
        if state.status != AuditStatus.COMPLETED:
            return state
        
        # Use the compliance score tool
        score_tool = next(t for t in AUDIT_TOOLS if t.name == "calculate_compliance_score")
        result = await score_tool._arun(session_id=state.session_id)
        
        if "compliance_score" in result:
            state.compliance_score = result["compliance_score"]
        
        state.updated_at = datetime.utcnow()
        return state
    
    async def generate_recommendations(self, state: AuditState) -> AuditState:
        """Generate recommendations based on audit findings"""
        if not state.compliance_score:
            return state
        
        # Use the recommendations tool
        rec_tool = next(t for t in AUDIT_TOOLS if t.name == "generate_recommendations")
        result = await rec_tool._arun(
            session_id=state.session_id,
            compliance_score=state.compliance_score
        )
        
        if "recommendations" in result:
            state.recommendations = result["recommendations"]
        
        state.updated_at = datetime.utcnow()
        return state
    
    async def create_audit_report(self, state: AuditState) -> AuditState:
        """Create final audit report"""
        if state.status != AuditStatus.COMPLETED:
            return state
        
        system_prompt = """You are an expert ISO 27001 auditor creating a final audit report. 
        Create a comprehensive, professional report based on the audit findings."""
        
        user_prompt = f"""
        Create an ISO 27001 audit report with the following information:
        
        Session ID: {state.session_id}
        Compliance Score: {state.compliance_score}%
        Total Clauses Audited: {state.total_clauses}
        Recommendations: {state.recommendations}
        
        User Answers Summary:
        {self._format_answers_summary(state.user_answers)}
        
        Please create a professional audit report with:
        1. Executive Summary
        2. Compliance Assessment
        3. Key Findings
        4. Recommendations
        5. Next Steps
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Store the report in audit findings
        state.audit_findings.append({
            "type": "final_report",
            "content": response.content,
            "generated_at": datetime.utcnow().isoformat()
        })
        
        state.updated_at = datetime.utcnow()
        return state
    
    def _format_answers_summary(self, user_answers: Dict[int, str]) -> str:
        """Format user answers for the report"""
        summary = []
        for clause_idx, answer in user_answers.items():
            if clause_idx < len(CLAUSE_METADATA):
                clause = CLAUSE_METADATA[clause_idx]
                summary.append(f"Clause {clause_idx + 1}: {clause['question']}")
                summary.append(f"Answer: {answer}")
                summary.append("")
        return "\n".join(summary) 