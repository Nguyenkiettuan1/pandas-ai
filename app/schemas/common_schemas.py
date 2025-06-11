from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

class CSVUploadRequest(BaseModel):
    name: str
    csv_file_path: str
    description: Optional[str] = None
