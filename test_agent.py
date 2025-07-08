#!/usr/bin/env python3
"""
Test script for the ISO 27001 Agentic Audit System
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


class AgenticAuditTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    async def start_audit(self) -> str:
        """Start a new agentic audit session"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/agent/start") as response:
                if response.status == 200:
                    data = await response.json()
                    self.session_id = data["session_id"]
                    print(f"✅ Started audit session: {self.session_id}")
                    return self.session_id
                else:
                    error = await response.text()
                    print(f"❌ Failed to start audit: {error}")
                    return None
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current audit status"""
        if not self.session_id:
            print("❌ No active session")
            return None
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/agent/{self.session_id}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"📊 Status: {data['status']}")
                    print(f"📋 Current clause: {data.get('current_clause_index', 0)}/{data.get('total_clauses', 0)}")
                    return data
                else:
                    error = await response.text()
                    print(f"❌ Failed to get status: {error}")
                    return None
    
    async def ask_question(self, question: str) -> str:
        """Ask a question about the current clause"""
        if not self.session_id:
            print("❌ No active session")
            return None
        
        async with aiohttp.ClientSession() as session:
            payload = {"query": question}
            async with session.post(
                f"{self.base_url}/agent/{self.session_id}/query",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"🤖 Agent: {data['response']}")
                    return data['response']
                else:
                    error = await response.text()
                    print(f"❌ Failed to ask question: {error}")
                    return None
    
    async def record_answer(self, answer: str) -> bool:
        """Record an answer for the current clause"""
        if not self.session_id:
            print("❌ No active session")
            return False
        
        async with aiohttp.ClientSession() as session:
            payload = {"answer": answer}
            async with session.post(
                f"{self.base_url}/agent/{self.session_id}/answer",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Recorded answer: {answer}")
                    return data.get('success', False)
                else:
                    error = await response.text()
                    print(f"❌ Failed to record answer: {error}")
                    return False
    
    async def upload_document(self, document_key: str) -> bool:
        """Upload a document for analysis"""
        if not self.session_id:
            print("❌ No active session")
            return False
        
        async with aiohttp.ClientSession() as session:
            payload = {"document_key": document_key}
            async with session.post(
                f"{self.base_url}/agent/{self.session_id}/upload-document",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"📄 Uploaded document: {document_key}")
                    return data.get('success', False)
                else:
                    error = await response.text()
                    print(f"❌ Failed to upload document: {error}")
                    return False
    
    async def get_report(self) -> Dict[str, Any]:
        """Get the final audit report"""
        if not self.session_id:
            print("❌ No active session")
            return None
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/agent/{self.session_id}/report") as response:
                if response.status == 200:
                    data = await response.json()
                    print("📋 Final Audit Report:")
                    print(f"   Compliance Score: {data.get('compliance_score', 0)}%")
                    print(f"   Recommendations: {len(data.get('recommendations', []))}")
                    return data
                else:
                    error = await response.text()
                    print(f"❌ Failed to get report: {error}")
                    return None


async def run_demo():
    """Run a demonstration of the agentic audit system"""
    print("🚀 Starting ISO 27001 Agentic Audit Demo")
    print("=" * 50)
    
    tester = AgenticAuditTester()
    
    # Start audit
    session_id = await tester.start_audit()
    if not session_id:
        return
    
    # Get initial status
    await tester.get_status()
    
    # Ask some questions
    questions = [
        "What does this clause require us to implement?",
        "How can we demonstrate compliance with this requirement?",
        "What are the key controls we need to have in place?"
    ]
    
    for question in questions:
        print(f"\n❓ User: {question}")
        await tester.ask_question(question)
        await asyncio.sleep(1)  # Small delay for readability
    
    # Record some answers
    answers = [
        "Yes, we have a documented scope statement that defines our ISMS boundaries",
        "We have identified internal and external issues through our context analysis",
        "Our leadership team has established an information security policy"
    ]
    
    for answer in answers:
        print(f"\n📝 Recording answer: {answer}")
        await tester.record_answer(answer)
        await asyncio.sleep(1)
    
    # Upload a document
    await tester.upload_document("security-policy.pdf")
    
    # Get final status
    await tester.get_status()
    
    # Try to get report (might not be complete yet)
    await tester.get_report()
    
    print("\n🎉 Demo completed!")


if __name__ == "__main__":
    asyncio.run(run_demo()) 