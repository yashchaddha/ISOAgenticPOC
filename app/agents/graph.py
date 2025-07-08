# app/agents/graph.py

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
import uuid
from datetime import datetime

from app.agents.state import AuditState, AuditStatus, create_initial_state
from app.agents.nodes import AuditNodes
from app.agents.tools import AUDIT_TOOLS
from app.services.mongo_client import db


class AuditGraph:
    """LangGraph for ISO 27001 audit workflow"""
    
    def __init__(self):
        self.nodes = AuditNodes()
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the audit workflow graph"""
        
        # Create the graph
        workflow = StateGraph(AuditState)
        
        # Add nodes
        workflow.add_node("initialize_session", self.nodes.initialize_session)
        workflow.add_node("get_current_clause", self.nodes.get_current_clause)
        workflow.add_node("process_user_query", self.nodes.process_user_query)
        workflow.add_node("record_user_answer", self.nodes.record_user_answer)
        workflow.add_node("analyze_documents", self.nodes.analyze_documents)
        workflow.add_node("advance_to_next_clause", self.nodes.advance_to_next_clause)
        workflow.add_node("calculate_compliance_score", self.nodes.calculate_compliance_score)
        workflow.add_node("generate_recommendations", self.nodes.generate_recommendations)
        workflow.add_node("create_audit_report", self.nodes.create_audit_report)
        
        # Define the main workflow
        workflow.set_entry_point("initialize_session")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "initialize_session",
            self._should_get_clause,
            {
                "get_clause": "get_current_clause",
                "complete": END
            }
        )
        
        workflow.add_conditional_edges(
            "get_current_clause",
            self._should_process_query,
            {
                "process_query": "process_user_query",
                "record_answer": "record_user_answer",
                "analyze_docs": "analyze_documents",
                "advance": "advance_to_next_clause",
                "complete": "calculate_compliance_score"
            }
        )
        
        workflow.add_conditional_edges(
            "process_user_query",
            self._should_continue_audit,
            {
                "continue": "get_current_clause",
                "complete": "calculate_compliance_score"
            }
        )
        
        workflow.add_conditional_edges(
            "record_user_answer",
            self._should_analyze_documents,
            {
                "analyze": "analyze_documents",
                "advance": "advance_to_next_clause"
            }
        )
        
        workflow.add_conditional_edges(
            "analyze_documents",
            self._should_advance,
            {
                "advance": "advance_to_next_clause",
                "complete": "calculate_compliance_score"
            }
        )
        
        workflow.add_conditional_edges(
            "advance_to_next_clause",
            self._should_continue_audit,
            {
                "continue": "get_current_clause",
                "complete": "calculate_compliance_score"
            }
        )
        
        # Final workflow
        workflow.add_edge("calculate_compliance_score", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "create_audit_report")
        workflow.add_edge("create_audit_report", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _should_get_clause(self, state: AuditState) -> str:
        """Determine if we should get the next clause"""
        if state.status == AuditStatus.IN_PROGRESS and state.current_clause_index < state.total_clauses:
            return "get_clause"
        return "complete"
    
    def _should_process_query(self, state: AuditState) -> str:
        """Determine the next action based on current state"""
        if state.current_query:
            return "process_query"
        elif hasattr(state, 'pending_answer') and state.pending_answer:
            return "record_answer"
        elif state.uploaded_documents and state.current_clause:
            return "analyze_docs"
        elif state.current_clause_index >= state.total_clauses:
            return "complete"
        else:
            return "advance"
    
    def _should_continue_audit(self, state: AuditState) -> str:
        """Determine if audit should continue"""
        if state.current_clause_index < state.total_clauses:
            return "continue"
        return "complete"
    
    def _should_analyze_documents(self, state: AuditState) -> str:
        """Determine if documents should be analyzed"""
        if state.uploaded_documents:
            return "analyze"
        return "advance"
    
    def _should_advance(self, state: AuditState) -> str:
        """Determine if we should advance to next clause"""
        if state.current_clause_index < state.total_clauses - 1:
            return "advance"
        return "complete"
    
    async def start_audit(self, session_id: Optional[str] = None) -> str:
        """Start a new audit session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create initial state
        initial_state = create_initial_state(session_id)
        
        # Save session to MongoDB
        await db.sessions.insert_one({
            "_id": session_id,
            "clause_index": 0,
            "created_at": initial_state.created_at,
            "status": initial_state.status.value
        })
        
        # Run the graph
        config = {"configurable": {"thread_id": session_id}}
        result = await self.graph.ainvoke(initial_state, config)
        
        return session_id
    
    async def process_query(self, session_id: str, query: str) -> Dict[str, Any]:
        """Process a user query in the context of the current audit"""
        config = {"configurable": {"thread_id": session_id}}
        
        # Get current state
        current_state = await self.graph.get_state(config)
        
        if not current_state:
            raise ValueError("Session not found")
        
        # Create a new state with the query
        from app.agents.state import AuditState
        new_state = AuditState(**current_state)
        new_state.current_query = query
        
        # Run the graph
        result = await self.graph.ainvoke(new_state, config)
        
        return {
            "response": result.agent_response,
            "current_clause": result.current_clause,
            "status": result.status.value
        }
    
    async def record_answer(self, session_id: str, answer: str) -> Dict[str, Any]:
        """Record a user answer for the current clause"""
        config = {"configurable": {"thread_id": session_id}}
        
        # Get current state
        current_state = await self.graph.get_state(config)
        
        if not current_state:
            raise ValueError("Session not found")
        
        # Create a new state with the answer
        from app.agents.state import AuditState
        new_state = AuditState(**current_state)
        new_state.pending_answer = answer
        
        # Run the graph
        result = await self.graph.ainvoke(new_state, config)
        
        return {
            "success": True,
            "next_clause": result.current_clause,
            "status": result.status.value
        }
    
    async def upload_document(self, session_id: str, document_key: str) -> Dict[str, Any]:
        """Add a document to the audit session"""
        config = {"configurable": {"thread_id": session_id}}
        
        # Get current state
        current_state = await self.graph.get_state(config)
        
        if not current_state:
            raise ValueError("Session not found")
        
        # Create a new state with the document
        from app.agents.state import AuditState
        new_state = AuditState(**current_state)
        if document_key not in new_state.uploaded_documents:
            new_state.uploaded_documents.append(document_key)
        
        # Run the graph to analyze documents
        result = await self.graph.ainvoke(new_state, config)
        
        return {
            "success": True,
            "document_analysis": result.document_analysis.get(result.current_clause_index, []),
            "status": result.status.value
        }
    
    async def get_audit_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of an audit session"""
        config = {"configurable": {"thread_id": session_id}}
        
        # Get current state
        current_state = await self.graph.get_state(config)
        
        if not current_state:
            raise ValueError("Session not found")
        
        # Convert to AuditState object
        from app.agents.state import AuditState
        state = AuditState(**current_state)
        
        return {
            "session_id": session_id,
            "status": state.status.value,
            "current_clause": state.current_clause,
            "current_clause_index": state.current_clause_index,
            "total_clauses": state.total_clauses,
            "compliance_score": state.compliance_score,
            "recommendations": state.recommendations,
            "uploaded_documents": state.uploaded_documents
        }
    
    async def get_audit_report(self, session_id: str) -> Dict[str, Any]:
        """Get the final audit report"""
        config = {"configurable": {"thread_id": session_id}}
        
        # Get current state
        current_state = await self.graph.get_state(config)
        
        if not current_state:
            raise ValueError("Session not found")
        
        # Convert to AuditState object
        from app.agents.state import AuditState
        state = AuditState(**current_state)
        
        if state.status != AuditStatus.COMPLETED:
            raise ValueError("Audit not completed")
        
        # Find the final report
        final_report = None
        for finding in state.audit_findings:
            if finding["type"] == "final_report":
                final_report = finding
                break
        
        return {
            "session_id": session_id,
            "compliance_score": state.compliance_score,
            "recommendations": state.recommendations,
            "user_answers": state.user_answers,
            "final_report": final_report["content"] if final_report else None,
            "generated_at": final_report["generated_at"] if final_report else None
        }


# Global instance
audit_graph = AuditGraph() 