from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class QueryRequest(BaseModel):
    question: str
    dataset_id: Optional[int] = None  # Make dataset_id optional for auto-detection
    session_id: Optional[str] = None
    
class EnhancedQueryRequest(BaseModel):
    """Enhanced query request with full context support"""
    question: str = Field(..., description="Natural language question")
    dataset_id: Optional[int] = Field(default=None, description="Explicit dataset ID (legacy mode)")
    session_id: Optional[str] = Field(default=None, description="Session context for dataset selection")
    workspace_id: Optional[str] = Field(default=None, description="Workspace context for dataset selection")
    auto_select: bool = Field(default=True, description="Enable automatic dataset selection")
    max_datasets: int = Field(default=3, description="Maximum datasets to use")
    context_hint: Optional[str] = Field(default=None, description="Hint for dataset selection")
    profile_name: Optional[str] = Field(default=None, description="Agent profile (auto-detect if not specified)")
    
    def needs_auto_dataset_selection(self) -> bool:
        """Check if automatic dataset selection is needed"""
        return self.dataset_id is None and self.auto_select
    
    def has_context(self) -> bool:
        """Check if any context is provided"""
        return any([self.session_id, self.workspace_id, self.dataset_id])

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
    dataset_id: Optional[int] = Field(default=None, description="Optional dataset ID for context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "doanh thu tháng này như thế nào?",
                "dataset_id": 1  # Optional
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