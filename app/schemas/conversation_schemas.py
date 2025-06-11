from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConversationResponse(BaseModel):
    id: int
    user_message: str
    assistant_response: str
    query_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True
