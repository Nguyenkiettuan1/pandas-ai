from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
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

class SuggestionsRequest(BaseModel):
    question: str = Field(..., description="The question to get agent suggestions for")
    dataset_id: int = Field(..., description="Dataset ID to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "doanh thu tháng này như thế nào?",
                "dataset_id": 1
            }
        }

class SuggestionsResponse(BaseModel):
    question: str
    dataset_id: int
    recommended_agent: str
    all_suggestions: list
    dataset_context: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "doanh thu tháng này như thế nào?",
                "dataset_id": 1,
                "recommended_agent": "sales_analyst",
                "all_suggestions": [
                    {
                        "agent": "sales_analyst",
                        "score": 0.85,
                        "description": "Chuyên gia phân tích bán hàng và doanh thu",
                        "confidence": "high"
                    }
                ],
                "dataset_context": {
                    "table_name": "sales_data",
                    "dataset_name": "Sales Dataset",
                    "description": "Monthly sales data"
                }
            }
        }