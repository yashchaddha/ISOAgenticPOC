# app/agents/simple_graph.py

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from app.services.mongo_client import db
from app.services.audit_engine import CLAUSE_METADATA
from app.agents.state import AuditState, AuditStatus, create_initial_state
from app.config import settings


class SimpleAuditGraph:
    """Simplified audit graph that works with current LangGraph version"""
    
    def __init__(self):
        self.sessions = {}  # In-memory session storage
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            max_tokens=1000,
            api_key=settings.openai_api_key
        )
    
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
        
        # Store in memory
        self.sessions[session_id] = initial_state
        
        # Set current clause
        if initial_state.current_clause_index < len(CLAUSE_METADATA):
            initial_state.current_clause = CLAUSE_METADATA[initial_state.current_clause_index]
        
        return session_id
    
    async def process_query(self, session_id: str, query: str) -> Dict[str, Any]:
        """Process a user query"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        
        state = self.sessions[session_id]
        state.current_query = query
        
        # New system prompt: always return JSON with response, advance_clause, and previous_clause
        system_prompt = '''
You are an expert ISO 27001 internal auditor chatbot. For every user message, you must return a JSON object with three fields:
- response: your answer to the user's question (string)
- advance_clause: true if the user wants to move to the next clause, false otherwise (boolean)
- previous_clause: true if the user wants to move to the previous clause, false otherwise (boolean)

If the user message is a request to move to the next clause (e.g., "next", "skip", "move to next clause", "advance", etc.), set advance_clause to true.
If the user message is a request to move to the previous clause (e.g., "previous", "back", "go back", "move to previous clause", etc.), set previous_clause to true.
If neither, set both to false.

At the end of every response, always ask: "Would you like to record your answer for this clause or upload supporting documents?"
If the user answers 'No' or expresses intent not to record or upload, respond with: "Are you facing any issues or challenges related to this clause? I can help clarify or provide guidance."

Always return a valid JSON object. Example:
{"response": "Here is my answer... Would you like to record your answer for this clause or upload supporting documents?", "advance_clause": false, "previous_clause": false}
'''
        
        user_prompt = f'''
Current Clause: {state.current_clause['question'] if state.current_clause else ''}
Description: {state.current_clause['description'] if state.current_clause else ''}
Key Attributes: {', '.join(state.current_clause['attributes']) if state.current_clause else ''}

User Message: {query}
'''
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        import json
        try:
            llm_response = await self.llm.ainvoke(messages)
            # Try to parse the LLM output as JSON
            try:
                result = json.loads(llm_response.content)
                response_text = result.get('response', llm_response.content)
                advance_clause = result.get('advance_clause', False)
                previous_clause = result.get('previous_clause', False)
            except Exception:
                response_text = llm_response.content
                advance_clause = False
                previous_clause = False
        except Exception as e:
            response_text = f"I apologize, but I encountered an error while processing your query. Please try again. Error: {str(e)}"
            advance_clause = False
            previous_clause = False
        
        # If LLM says to advance, call record_answer with skip
        if advance_clause:
            await self.record_answer(session_id, '__skip__')
            # Update state after advancing
            state = self.sessions[session_id]
        # If LLM says to go to previous, set clause index to previous (if possible)
        elif previous_clause:
            if state.current_clause_index > 0:
                await self.set_clause_index(session_id, state.current_clause_index - 1)
                state = self.sessions[session_id]

        state.agent_response = response_text
        state.updated_at = datetime.utcnow()
        
        # Add to conversation history
        state.conversation_history.append({
            "role": "user",
            "content": query,
            "timestamp": datetime.utcnow().isoformat()
        })
        state.conversation_history.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "response": response_text,
            "advance_clause": advance_clause,
            "previous_clause": previous_clause,
            "current_clause": state.current_clause,
            "status": state.status.value
        }
    
    async def record_answer(self, session_id: str, answer: str) -> Dict[str, Any]:
        """Record a user answer"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        
        state = self.sessions[session_id]
        
        if state.current_clause_index >= len(CLAUSE_METADATA):
            raise ValueError("No more clauses to answer")
        
        # Record the answer
        state.user_answers[state.current_clause_index] = answer
        
        # Save to MongoDB
        await db.responses.insert_one({
            "session_id": session_id,
            "clause_index": state.current_clause_index,
            "clause": state.current_clause["question"],
            "answer": answer,
            "answered_at": datetime.utcnow()
        })
        
        # Advance to next clause
        state.current_clause_index += 1
        
        if state.current_clause_index >= len(CLAUSE_METADATA):
            state.status = AuditStatus.COMPLETED
            state.current_clause = None
        else:
            state.current_clause = CLAUSE_METADATA[state.current_clause_index]
        
        # Update MongoDB
        await db.sessions.update_one(
            {"_id": session_id},
            {"$inc": {"clause_index": 1}}
        )
        
        state.updated_at = datetime.utcnow()
        
        return {
            "success": True,
            "next_clause": state.current_clause,
            "status": state.status.value
        }
    
    async def get_audit_status(self, session_id: str) -> Dict[str, Any]:
        """Get audit status"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        
        state = self.sessions[session_id]
        
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
    
    async def upload_document(self, session_id: str, document_key: str) -> Dict[str, Any]:
        """Upload document for analysis"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        
        state = self.sessions[session_id]
        
        if document_key not in state.uploaded_documents:
            state.uploaded_documents.append(document_key)
        
        # Generate LLM-based document analysis
        if state.current_clause:
            system_prompt = """You are an expert ISO 27001 auditor analyzing uploaded documents for compliance. 
            
            First check if the document is related to ISO 27001. If it is not, politely tell the user that you can only analyze documents related to ISO 27001.
            
            If it is related to ISO 27001, then:
            Provide a detailed, structured analysis of how well the document addresses the current clause requirements.
            Be specific, professional, and actionable in your assessment."""
            
            user_prompt = f"""
            **Current Clause Analysis Request**
            
            **Clause:** {state.current_clause['question']}
            **Description:** {state.current_clause['description']}
            **Key Requirements:** {', '.join(state.current_clause['attributes'])}
            
            **Document to Analyze:** {document_key}
            
            Please provide a comprehensive analysis covering:
            
            1. **Compliance Assessment:** Does this document adequately address the current clause requirements?
            2. **Key Findings:** What specific evidence of compliance or non-compliance did you identify?
            3. **Strengths:** What aspects of the document demonstrate good compliance practices?
            4. **Gaps/Concerns:** What areas need improvement or are missing?
            5. **Recommendations:** What specific actions should be taken to improve compliance?
            6. **Confidence Level:** How confident are you in this assessment (High/Medium/Low)?
            
            Format your response in a clear, structured manner that an auditor would find useful.
            
            .
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            try:
                response = await self.llm.ainvoke(messages)
                analysis_summary = response.content
            except Exception as e:
                analysis_summary = f"Document analysis completed. Note: LLM analysis encountered an error: {str(e)}"
        else:
            analysis_summary = "Document uploaded successfully."
        
        analysis = {
            "document_key": document_key,
            "compliance_found": True,
            "relevant_sections": ["Document analysis completed"],
            "confidence_score": 0.85,
            "analysis_summary": analysis_summary
        }
        
        state.document_analysis[state.current_clause_index] = [analysis]
        state.updated_at = datetime.utcnow()

        # Store document upload in MongoDB with clause and answer
        # Try to get the answer for the current clause, or the previous clause if just advanced
        user_answer = None
        if state.user_answers.get(state.current_clause_index) is not None:
            user_answer = state.user_answers[state.current_clause_index]
        elif state.user_answers.get(state.current_clause_index - 1) is not None and state.current_clause_index > 0:
            user_answer = state.user_answers[state.current_clause_index - 1]
        doc_to_insert = {
            "session_id": session_id,
            "clause_index": state.current_clause_index,
            "clause": state.current_clause["question"] if state.current_clause else None,
            "document_key": document_key,
            "analysis_summary": analysis_summary,
            "answer": user_answer,
            "uploaded_at": datetime.utcnow()
        }
        print(f"[DEBUG] Inserting document into db.documents: {doc_to_insert}")
        await db.documents.insert_one(doc_to_insert)
        
        return {
            "success": True,
            "document_analysis": [analysis],
            "status": state.status.value
        }
    
    async def get_audit_report(self, session_id: str) -> Dict[str, Any]:
        """Get final audit report"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        
        state = self.sessions[session_id]
        
        if state.status != AuditStatus.COMPLETED:
            raise ValueError("Audit not completed")
        
        # Calculate compliance score
        total_responses = len(state.user_answers)
        positive_keywords = ["yes", "implemented", "compliant", "adequate", "sufficient"]
        
        positive_count = 0
        for answer in state.user_answers.values():
            answer_lower = answer.lower()
            if any(keyword in answer_lower for keyword in positive_keywords):
                positive_count += 1
        
        compliance_score = (positive_count / total_responses) * 100 if total_responses > 0 else 0
        
        # Generate recommendations
        recommendations = []
        if compliance_score < 70:
            recommendations.append("Implement comprehensive ISMS framework")
            recommendations.append("Conduct staff training on information security")
        
        return {
            "session_id": session_id,
            "compliance_score": compliance_score,
            "recommendations": recommendations,
            "user_answers": state.user_answers,
            "final_report": f"Audit completed with {compliance_score}% compliance score.",
            "generated_at": datetime.utcnow().isoformat()
        }

    async def set_clause_index(self, session_id: str, index: int) -> dict:
        """Set the current clause index for navigation (e.g., previous/next clause)"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        if not (0 <= index < len(CLAUSE_METADATA)):
            raise ValueError("Invalid clause index")
        state = self.sessions[session_id]
        state.current_clause_index = index
        state.current_clause = CLAUSE_METADATA[index]
        # Optionally update MongoDB as well
        await db.sessions.update_one({"_id": session_id}, {"$set": {"clause_index": index}})
        state.updated_at = datetime.utcnow()
        return {"current_clause_index": state.current_clause_index}


# Global instance
simple_audit_graph = SimpleAuditGraph() 