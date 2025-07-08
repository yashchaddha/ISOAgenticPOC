# app/services/audit_engine.py

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from app.services.mongo_client import db

# -----------------------------------------------------------------------------
# Load environment variables and initialize OpenAI client
# -----------------------------------------------------------------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise OpenAIError("OPENAI_API_KEY environment variable is not set")
client = OpenAI(api_key=api_key)

# -----------------------------------------------------------------------------
# Clause metadata: questions, descriptions, attributes
# -----------------------------------------------------------------------------
CLAUSE_METADATA = [
    {
        "question": "Clause 4.1: What is the scope of the ISMS?",
        "description": (
            "This clause requires defining the boundaries and applicability of "
            "the Information Security Management System, including interfaces "
            "and dependencies with external parties."
        ),
        "attributes": [
            "Scope statement",
            "Interfaces & dependencies",
            "Excluded areas"
        ],
    },
    {
        "question": "Clause 4.2: What are the internal and external issues?",
        "description": (
            "Identify internal and external factors that can affect the ability "
            "to achieve the intended outcome(s) of the ISMS."
        ),
        "attributes": [
            "Internal contexts",
            "External contexts",
            "Interested parties’ needs"
        ],
    },
    {
        "question": "Clause 5.1: How is leadership demonstrating commitment?",
        "description": (
            "Top management must demonstrate leadership and commitment by being "
            "accountable for the effectiveness of the ISMS, establishing policy, "
            "assigning roles, and promoting continual improvement."
        ),
        "attributes": [
            "Information security policy",
            "Roles & responsibilities",
            "Resource provision"
        ],
    },
    {
        "question": "Clause 5.2: How is leadership demonstrating commitment?",
        "description": (
            "Top management must demonstrate leadership and commitment by being "
            "accountable for the effectiveness of the ISMS, establishing policy, "
            "assigning roles, and promoting continual improvement."
        ),
        "attributes": [
            "Information security policy",
            "Roles & responsibilities",
            "Resource provision"
        ],
    },
    {
        "question": "Clause 5.3: How is leadership demonstrating commitment?",
        "description": (
            "Top management must demonstrate leadership and commitment by being "
            "accountable for the effectiveness of the ISMS, establishing policy, "
            "assigning roles, and promoting continual improvement."
        ),
        "attributes": [
            "Information security policy",
            "Roles & responsibilities",
            "Resource provision"
        ],
    },
    # …add remaining clause entries as needed…
]

# -----------------------------------------------------------------------------
# AuditEngine: session, next clause, record answer, handle query
# -----------------------------------------------------------------------------
class AuditEngine:
    
    async def create_session() -> str:
        """
        Initialize a new audit session in MongoDB.
        """
        session_id = str(uuid.uuid4())
        await db.sessions.insert_one({
            "_id": session_id,
            "clause_index": 0
        })
        return session_id

    @staticmethod
    async def next_clause(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for the next clause in this session.
        Returns None if all clauses have been completed.
        """
        sess = await db.sessions.find_one({"_id": session_id})
        if not sess:
            raise KeyError("Session not found")

        idx = sess.get("clause_index", 0)
        if idx >= len(CLAUSE_METADATA):
            return None

        return CLAUSE_METADATA[idx]

    @staticmethod
    async def record_answer(session_id: str, answer: str):
        """
        Save the user's answer for the current clause into the 'responses' collection,
        then advance the session to the next clause.
        """
        sess = await db.sessions.find_one({"_id": session_id})
        if not sess:
            raise KeyError("Session not found")

        idx = sess.get("clause_index", 0)
        if idx >= len(CLAUSE_METADATA):
            raise IndexError("No more clauses to answer")

        clause_text = CLAUSE_METADATA[idx]["question"]

        await db.responses.insert_one({
            "session_id": session_id,
            "clause_index": idx,
            "clause": clause_text,
            "answer": answer,
            "answered_at": datetime.utcnow()
        })

        await db.sessions.update_one(
            {"_id": session_id},
            {"$inc": {"clause_index": 1}}
        )

    @staticmethod
    async def handle_query(session_id: str, user_query: str) -> str:
        """
        Use the OpenAI v1 client to answer a free-form question about the current clause.
        """
        meta = await AuditEngine.next_clause(session_id)
        if not meta:
            return "Audit complete. No active clause."

        system_prompt = "You are an expert ISO 27001 internal auditor. If the query is not related to the ISO 27001, politely tell the user that you can only answer questions related to ISO 27001 clauses. At the end of each answer, ask the user if they want to submit documents related to the clause or record their answer for it"
        user_prompt = (
            f"Clause description: {meta['description']}\n"
            f"Attributes: {', '.join(meta['attributes'])}\n"
            f"User asks: {user_query}\n"
            "Provide a clear, concise answer."
        )

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0
        )

        return response.choices[0].message.content.strip()
