from fastapi import APIRouter, Depends, HTTPException, Query as FastAPIQuery
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.response_handler import ResponseHandler, ResponseType
from app.services.query_service import QueryService
from app.schemas.query_schemas import QueryRequest, QueryResponse, QueryHistoryResponse

logger = get_logger(__name__)

# Create router for query endpoints
query_router = APIRouter(prefix="/queries", tags=["Queries"])

@query_router.post("/", response_model=Dict[str, Any])
async def process_query(
    query_request: QueryRequest,
    profile_name: Optional[str] = FastAPIQuery(default="general_analyst", description="Agent profile to use"),
    db: Session = Depends(get_db)
):
    """Process a natural language query with specified agent profile"""
    logger.info(f"Processing query with profile: {profile_name}")
    
    try:
        service = QueryService(db)
        
        # Validate parameters first
        validation_result = await service.validate_query_parameters(
            question=query_request.question,
            dataset_id=query_request.dataset_id,
            profile_name=profile_name
        )
        
        # Check if validation failed
        if not ResponseHandler.is_success(validation_result):
            return validation_result
        
        # Extract validated profile name
        validated_data = ResponseHandler.extract_data_safely(validation_result)
        final_profile = validated_data.get("validated_profile", profile_name)
        
        # Process the query
        result = await service.process_natural_language_query(
            question=query_request.question,
            dataset_id=query_request.dataset_id,
            session_id=query_request.session_id or str(uuid.uuid4()),
            profile_name=final_profile
        )
        
        logger.info(f"Query processed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error processing query: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error occurred while processing query",
            response_type=ResponseType.QUERY_RESULT
        )

@query_router.get("/history/", response_model=Dict[str, Any])
async def get_query_history(
    dataset_id: int = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get query history"""
    logger.info(f"Getting query history for dataset {dataset_id}, limit {limit}")
    
    try:
        service = QueryService(db)
        history_response = await service.get_query_history(dataset_id=dataset_id, limit=limit)
        logger.info(f"Successfully retrieved query history")
        return history_response
        
    except Exception as e:
        logger.error(f"Unexpected error getting query history: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to retrieve query history",
            response_type=ResponseType.QUERY_HISTORY
        )

@query_router.post("/insights/{dataset_id}", response_model=Dict[str, Any])
async def get_dataset_insights(
    dataset_id: int,
    profile_name: Optional[str] = FastAPIQuery(default="general_analyst", description="Agent profile to use"),
    db: Session = Depends(get_db)
):
    """Get automated insights for a dataset"""
    logger.info(f"Generating insights for dataset {dataset_id} with profile {profile_name}")
    
    try:
        service = QueryService(db)
        insights_response = await service.get_dataset_insights(dataset_id, profile_name)
        logger.info(f"Generated insights for dataset {dataset_id}")
        return insights_response
        
    except Exception as e:
        logger.error(f"Unexpected error generating insights: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to generate dataset insights",
            response_type=ResponseType.DATASET_INSIGHT
        )

@query_router.get("/statistics/", response_model=Dict[str, Any])
async def get_query_statistics(
    dataset_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get query statistics"""
    logger.info(f"Getting query statistics for dataset {dataset_id}")
    
    try:
        service = QueryService(db)
        stats_response = await service.get_query_statistics(dataset_id)
        logger.info("Successfully retrieved query statistics")
        return stats_response
        
    except Exception as e:
        logger.error(f"Unexpected error getting query statistics: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to retrieve query statistics",
            response_type=ResponseType.GENERAL
        )

@query_router.get("/health/", response_model=Dict[str, Any])
async def get_service_health(db: Session = Depends(get_db)):
    """Get service health status"""
    logger.info("Checking service health")
    
    try:
        service = QueryService(db)
        health_response = await service.get_service_health()
        logger.info("Service health check completed")
        return health_response
        
    except Exception as e:
        logger.error(f"Unexpected error during health check: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Health check failed",
            response_type=ResponseType.GENERAL
        )
