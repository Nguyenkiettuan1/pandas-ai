from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class QueryRequest(BaseModel):
    question: str
    dataset_id: int
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    query_id: int
    question: str
    result: Any
    execution_time: int
    dataset_id: int

class QueryHistoryResponse(BaseModel):
    id: int
    question: str
    result: str
    execution_time: int
    dataset_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
