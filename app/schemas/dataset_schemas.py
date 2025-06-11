from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    table_name: Optional[str] = None

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    file_path: Optional[str]
    table_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True
