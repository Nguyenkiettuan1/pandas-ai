from fastapi import APIRouter, Depends, HTTPException, Query as FastAPIQuery
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.response_handler import ResponseHandler, ResponseType
from app.services.query_service import QueryService
from app.schemas.query_schemas import QueryRequest, QueryResponse, QueryHistoryResponse, SuggestionsRequest
from app.agents.agent_router import agent_router  # Add this import

logger = get_logger(__name__)

# Create router for query endpoints
query_router = APIRouter(prefix="/queries", tags=["Queries"])

@query_router.post("/suggestions/", response_model=Dict[str, Any])
async def get_agent_suggestions(
    suggestions_request: SuggestionsRequest,
    db: Session = Depends(get_db)
):
    """Get AI agent suggestions for a question"""
    logger.info(f"Getting agent suggestions for question: {suggestions_request.question[:50]}...")
    
    try:
        service = QueryService(db)
        
        # Validate dataset exists
        dataset = await service.get_dataset_by_id(suggestions_request.dataset_id)
        if not dataset:
            return ResponseHandler.create_error_response(
                error=ValueError(f"Dataset {suggestions_request.dataset_id} not found"),
                message="Dataset not found",
                response_type=ResponseType.VALIDATION_ERROR
            )
        
        # Get dataset context
        dataset_context = {
            'table_name': dataset.get('table_name', ''),
            'dataset_name': dataset.get('name', ''),
            'description': dataset.get('description', '')
        }
        
        # Get suggestions from agent router
        suggestions = agent_router.get_agent_suggestions(suggestions_request.question, top_n=5)
        recommended = agent_router.route_question(suggestions_request.question, dataset_context)
        
        response_data = {
            "question": suggestions_request.question,
            "dataset_id": suggestions_request.dataset_id,
            "recommended_agent": recommended.value,
            "all_suggestions": suggestions,
            "dataset_context": dataset_context
        }
        
        return ResponseHandler.create_success_response(
            data=response_data,
            message="Agent suggestions retrieved successfully",
            response_type=ResponseType.AGENT_SUGGESTIONS
        )
        
    except Exception as e:
        logger.error(f"Error getting agent suggestions: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to get agent suggestions",
            response_type=ResponseType.AGENT_SUGGESTIONS
        )

@query_router.post("/", response_model=Dict[str, Any])
async def process_query(
    query_request: QueryRequest,
    profile_name: Optional[str] = FastAPIQuery(default=None, description="Agent profile to use (auto-detect if not specified)"),
    db: Session = Depends(get_db)
):
    """Process a natural language query with auto-routing or specified agent profile"""
    logger.info(f"Processing query with profile: {profile_name or 'auto-detect'}")
    
    try:
        service = QueryService(db)
        
        # Auto-route if profile not specified
        final_profile = profile_name
        auto_routed = False
        
        if not profile_name:
            # Get dataset context for routing
            dataset = await service.get_dataset_by_id(query_request.dataset_id)
            if dataset:
                dataset_context = {
                    'table_name': dataset.get('table_name', ''),
                    'dataset_name': dataset.get('name', ''),
                    'description': dataset.get('description', '')
                }
                
                # Auto-route to best agent
                suggested_agent = agent_router.route_question(query_request.question, dataset_context)
                final_profile = suggested_agent.value
                auto_routed = True
                logger.info(f"Auto-routed to agent: {final_profile}")
            else:
                final_profile = "general_analyst"  # Fallback
        
        # Validate parameters
        validation_result = await service.validate_query_parameters(
            question=query_request.question,
            dataset_id=query_request.dataset_id,
            profile_name=final_profile
        )
        
        # Check if validation failed
        if not ResponseHandler.is_success(validation_result):
            return validation_result
        
        # Extract validated profile name
        validated_data = ResponseHandler.extract_data_safely(validation_result)
        validated_profile = validated_data.get("validated_profile", final_profile)
        
        # Process the query
        result = await service.process_natural_language_query(
            question=query_request.question,
            dataset_id=query_request.dataset_id,
            session_id=query_request.session_id or str(uuid.uuid4()),
            profile_name=validated_profile
        )
        
        # Add routing information to response
        if ResponseHandler.is_success(result):
            result_data = ResponseHandler.extract_data_safely(result)
            result_data["auto_routed"] = auto_routed
            result_data["profile_used"] = validated_profile
            
            result = ResponseHandler.create_success_response(
                data=result_data,
                message=result.get("message", "Query processed successfully"),
                response_type=result.get("response_type", ResponseType.QUERY_RESULT)
            )
        
        logger.info(f"Query processed successfully with agent: {validated_profile}")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error processing query: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error occurred while processing query",
            response_type=ResponseType.QUERY_RESULT
        )

@query_router.get("/agents/", response_model=Dict[str, Any])
async def get_available_agents():
    """Get list of available AI agents and their capabilities"""
    logger.info("Getting available agents")
    
    try:
        agents_info = []
        for agent_type, capability in agent_router.agent_capabilities.items():
            agents_info.append({
                "name": agent_type.value,
                "description": capability.description,
                "weight": capability.weight,
                "sample_keywords": capability.keywords[:5],  # First 5 keywords as examples
                "sample_patterns": [p for p in capability.patterns[:3]]  # First 3 patterns as examples
            })
        
        response_data = {
            "available_agents": agents_info,
            "total_agents": len(agents_info),
            "default_agent": "general_analyst"
        }
        
        return ResponseHandler.create_success_response(
            data=response_data,
            message="Available agents retrieved successfully",
            response_type=ResponseType.GENERAL
        )
        
    except Exception as e:
        logger.error(f"Error getting available agents: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to get available agents",
            response_type=ResponseType.GENERAL
        )

# ...existing endpoints remain the same...
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