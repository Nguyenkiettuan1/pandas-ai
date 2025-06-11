# Enhanced Query Schemas with Context Support
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID

# Import existing schemas to extend them
from app.schemas.query_schemas import QueryRequest as BaseQueryRequest, QueryResponse


class ContextDataset(BaseModel):
    """Dataset information with context metadata"""
    id: int
    role: str = Field(default="primary", description="Dataset role: primary, secondary, reference")
    tags: Optional[List[str]] = Field(default=None, description="Tags for smart selection")
    priority: int = Field(default=0, description="Selection priority")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class SessionCreateRequest(BaseModel):
    """Request to create a new session"""
    name: str = Field(..., description="Session name")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    default_dataset_id: Optional[int] = Field(default=None, description="Default dataset for this session")
    context_datasets: Optional[List[ContextDataset]] = Field(default=None, description="Datasets available in this session")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="Session-specific settings")
    expires_in_hours: Optional[int] = Field(default=24, description="Session expiration time in hours")


class SessionResponse(BaseModel):
    """Session information response"""
    id: UUID
    name: str
    user_id: Optional[str]
    default_dataset_id: Optional[int]
    context_datasets: Optional[List[ContextDataset]]
    settings: Optional[Dict[str, Any]]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool


class WorkspaceCreateRequest(BaseModel):
    """Request to create a new workspace"""
    name: str = Field(..., description="Workspace name")
    description: Optional[str] = Field(default=None, description="Workspace description")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    datasets: Optional[List[ContextDataset]] = Field(default=None, description="Initial datasets for workspace")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="Workspace-specific settings")


class WorkspaceResponse(BaseModel):
    """Workspace information response"""
    id: UUID
    name: str
    description: Optional[str]
    user_id: Optional[str]
    settings: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class EnhancedQueryRequest(BaseModel):
    """
    Enhanced query request supporting multiple context types
    Maintains backward compatibility with existing QueryRequest
    """
    question: str = Field(..., description="Natural language question")
    
    # Legacy mode - explicit dataset
    dataset_id: Optional[int] = Field(default=None, description="Explicit dataset ID (legacy mode)")
    
    # Context modes
    session_id: Optional[Union[str, UUID]] = Field(default=None, description="Session context")
    workspace_id: Optional[Union[str, UUID]] = Field(default=None, description="Workspace context")
    
    # Smart selection options
    auto_select: bool = Field(default=True, description="Enable automatic dataset selection")
    scope: str = Field(default="single", description="Query scope: single, multi, cross_dataset")
    context_hint: Optional[str] = Field(default=None, description="Context hint for dataset selection")
    
    # Additional options
    max_datasets: int = Field(default=3, description="Maximum datasets to use in auto-selection")
    include_metadata: bool = Field(default=False, description="Include dataset selection metadata in response")

    @validator('scope')
    def validate_scope(cls, v):
        allowed_scopes = ['single', 'multi', 'cross_dataset', 'discovery']
        if v not in allowed_scopes:
            raise ValueError(f"Scope must be one of: {allowed_scopes}")
        return v

    @validator('max_datasets')
    def validate_max_datasets(cls, v):
        if v < 1 or v > 10:
            raise ValueError("max_datasets must be between 1 and 10")
        return v

    def has_explicit_dataset(self) -> bool:
        """Check if explicit dataset_id is provided (legacy mode)"""
        return self.dataset_id is not None

    def has_session_context(self) -> bool:
        """Check if session context is provided"""
        return self.session_id is not None

    def has_workspace_context(self) -> bool:
        """Check if workspace context is provided"""
        return self.workspace_id is not None

    def needs_auto_selection(self) -> bool:
        """Check if automatic dataset selection is needed"""
        return (not self.has_explicit_dataset() and 
                not self.has_session_context() and 
                not self.has_workspace_context() and 
                self.auto_select)


class DatasetSelectionMetadata(BaseModel):
    """Metadata about how datasets were selected for a query"""
    strategy: str = Field(..., description="Selection strategy used")
    selected_datasets: List[int] = Field(..., description="Dataset IDs that were selected")
    selection_scores: Optional[Dict[int, float]] = Field(default=None, description="Selection confidence scores")
    reasoning: Optional[str] = Field(default=None, description="Human-readable selection reasoning")
    alternatives: Optional[List[int]] = Field(default=None, description="Alternative datasets considered")


class EnhancedQueryResponse(QueryResponse):
    """
    Enhanced query response with context information
    Extends existing QueryResponse
    """
    # Add context information
    context_type: Optional[str] = Field(default=None, description="Type of context used: explicit, session, workspace, auto")
    session_id: Optional[UUID] = Field(default=None, description="Session ID if used")
    workspace_id: Optional[UUID] = Field(default=None, description="Workspace ID if used")
    
    # Dataset selection information
    dataset_selection: Optional[DatasetSelectionMetadata] = Field(default=None, description="How datasets were selected")
    
    # Performance information
    context_resolution_time: Optional[float] = Field(default=None, description="Time to resolve context (seconds)")


class QuerySuggestionRequest(BaseModel):
    """Request for query suggestions based on context"""
    session_id: Optional[Union[str, UUID]] = Field(default=None, description="Session context")
    workspace_id: Optional[Union[str, UUID]] = Field(default=None, description="Workspace context")
    dataset_id: Optional[int] = Field(default=None, description="Specific dataset")
    context_hint: Optional[str] = Field(default=None, description="Context hint for suggestions")
    max_suggestions: int = Field(default=5, description="Maximum number of suggestions")


class QuerySuggestion(BaseModel):
    """Individual query suggestion"""
    question: str = Field(..., description="Suggested question")
    description: Optional[str] = Field(default=None, description="Description of what this query does")
    complexity: str = Field(default="simple", description="Query complexity: simple, medium, complex")
    estimated_datasets: List[int] = Field(default=[], description="Datasets likely needed for this query")
    confidence: float = Field(default=0.5, description="Confidence score for this suggestion")


class QuerySuggestionsResponse(BaseModel):
    """Response containing query suggestions"""
    suggestions: List[QuerySuggestion]
    context_type: str = Field(..., description="Type of context used for suggestions")
    total_suggestions: int
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
