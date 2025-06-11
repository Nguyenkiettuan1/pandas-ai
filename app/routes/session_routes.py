# Session Management Routes
from fastapi import APIRouter, Depends, HTTPException, Query as FastAPIQuery
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.response_handler import ResponseHandler, ResponseType
from app.core.logging_config import get_logger
from app.services.context_service import ContextService
from app.schemas.context_schemas import (
    SessionCreateRequest, SessionResponse,
    WorkspaceCreateRequest, WorkspaceResponse
)

logger = get_logger(__name__)

# Create router for session endpoints
session_router = APIRouter(prefix="/sessions", tags=["Sessions"])


@session_router.post("/", response_model=Dict[str, Any])
async def create_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new session with context information
    
    Sessions allow users to work with multiple datasets without explicitly 
    specifying dataset_id in each query.
    """
    logger.info(f"Creating session: {request.name}")
    
    try:
        service = ContextService(db)
        result = await service.create_session(request)
        
        if ResponseHandler.is_success(result):
            logger.info(f"Successfully created session: {request.name}")
        else:
            logger.warning(f"Failed to create session: {request.name}")
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error creating session: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to create session",
            response_type=ResponseType.GENERAL
        )


@session_router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get session information by ID"""
    logger.info(f"Getting session: {session_id}")
    
    try:
        service = ContextService(db)
        result = await service.get_session(session_id)
        
        if ResponseHandler.is_success(result):
            logger.info(f"Successfully retrieved session: {session_id}")
        else:
            logger.warning(f"Failed to retrieve session: {session_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error getting session {session_id}: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to retrieve session",
            response_type=ResponseType.GENERAL
        )


@session_router.get("/", response_model=Dict[str, Any])
async def list_sessions(
    user_id: Optional[str] = FastAPIQuery(default=None, description="Filter by user ID"),
    active_only: bool = FastAPIQuery(default=True, description="Show only active sessions"),
    limit: int = FastAPIQuery(default=20, ge=1, le=100, description="Maximum number of sessions to return"),
    db: Session = Depends(get_db)
):
    """List sessions with optional filtering"""
    logger.info(f"Listing sessions - user_id: {user_id}, active_only: {active_only}")
    
    try:
        # This would be implemented in ContextService
        # For now, return a placeholder response
        return ResponseHandler.create_success_response(
            data={"sessions": [], "total": 0},
            message="Session listing not yet implemented",
            response_type=ResponseType.GENERAL
        )
        
    except Exception as e:
        logger.error(f"Unexpected error listing sessions: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to list sessions",
            response_type=ResponseType.GENERAL
        )


@session_router.delete("/{session_id}", response_model=Dict[str, Any])
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Deactivate a session"""
    logger.info(f"Deleting session: {session_id}")
    
    try:
        # This would be implemented in ContextService
        # For now, return a placeholder response
        return ResponseHandler.create_success_response(
            data={"session_id": session_id, "deactivated": True},
            message="Session deletion not yet fully implemented",
            response_type=ResponseType.GENERAL
        )
        
    except Exception as e:
        logger.error(f"Unexpected error deleting session {session_id}: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to delete session",
            response_type=ResponseType.GENERAL
        )
