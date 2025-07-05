from pydantic import BaseModel
from typing import List,Optional

class StartAuditResponse(BaseModel):
    session_id: str

class QuestionResponse(BaseModel):
    question: str
    description: str         # new
    attributes: List[str] 

class AnswerRequest(BaseModel):
    answer: str


class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

