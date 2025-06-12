from fastapi import APIRouter, Depends, HTTPException, Query as FastAPIQuery
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.response_handler import ResponseHandler, ResponseType
from app.services.query_service import QueryService
from app.services.query_intent_analyzer import QueryIntentAnalyzer  # Add this import
from app.schemas.query_schemas import QueryRequest, QueryResponse, QueryHistoryResponse, SuggestionsRequest, EnhancedQueryRequest
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
        
        if suggestions_request.dataset_id:
            # Traditional mode with explicit dataset
            result = await service.get_agent_suggestions(
                question=suggestions_request.question,
                dataset_id=suggestions_request.dataset_id
            )
        else:
            # Context-free suggestions based only on question analysis
            logger.info("No dataset_id provided, giving general agent suggestions")
            
            # Use QueryIntentAnalyzer for context-free analysis
            analyzer = QueryIntentAnalyzer()
            analysis = analyzer.analyze_complete_query(suggestions_request.question)
            
            # Get agent suggestions from agent router
            suggestions = agent_router.get_agent_suggestions(suggestions_request.question, top_n=5)
            
            response_data = {
                "question": suggestions_request.question,
                "dataset_id": None,
                "recommended_agent": suggestions[0]["agent"] if suggestions else "general_analyst",
                "all_suggestions": suggestions,
                "intent_analysis": analysis,
                "dataset_context": None,
                "mode": "context_free"
            }
            
            result = ResponseHandler.create_success_response(
                data=response_data,
                message="Agent suggestions retrieved successfully (context-free mode)",
                response_type=ResponseType.AGENT_SUGGESTIONS
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error getting agent suggestions: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error occurred while getting agent suggestions",
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
        
        # Check if dataset_id is provided (legacy mode)
        if query_request.dataset_id:
            # Legacy mode: explicit dataset_id provided
            validation_result = await service.validate_query_parameters(
                question=query_request.question,
                dataset_id=query_request.dataset_id,
                profile_name=profile_name
            )
            
            if not ResponseHandler.is_success(validation_result):
                return validation_result
            
            validated_data = ResponseHandler.extract_data_safely(validation_result)
            final_profile = validated_data.get("validated_profile", "general_analyst")
            auto_routed = validated_data.get("is_auto_routed", False)
            
            # Process with explicit dataset
            result = await service.process_natural_language_query(
                question=query_request.question,
                dataset_id=query_request.dataset_id,
                session_id=query_request.session_id or str(uuid.uuid4()),
                profile_name=final_profile
            )
            
            # Add routing information to response
            if ResponseHandler.is_success(result):
                result_data = ResponseHandler.extract_data_safely(result)
                result_data["auto_routed"] = auto_routed
                result_data["profile_used"] = final_profile
                result_data["mode"] = "legacy_explicit"
                
                result = ResponseHandler.create_success_response(
                    data=result_data,
                    message=result.get("message", "Query processed successfully"),
                    response_type=result.get("response_type", ResponseType.QUERY_RESULT)
                )
        else:
            # Auto-detection mode: no explicit dataset_id provided
            logger.info("No dataset_id provided, using auto-detection mode")
            
            # Use context-aware query processing
            result = await service.process_context_aware_query(
                question=query_request.question,
                session_id=query_request.session_id,
                auto_select=True,
                max_datasets=3,
                profile_name=profile_name
            )
            
            # Add mode information to response
            if ResponseHandler.is_success(result):
                result_data = ResponseHandler.extract_data_safely(result)
                result_data["mode"] = "auto_detection"
                
                result = ResponseHandler.create_success_response(
                    data=result_data,
                    message=result.get("message", "Query processed successfully with auto-detection"),
                    response_type=result.get("response_type", ResponseType.QUERY_RESULT)
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

@query_router.post("/enhanced/", response_model=Dict[str, Any])
async def process_enhanced_query(
    query_request: EnhancedQueryRequest,
    db: Session = Depends(get_db)
):
    """Process query with full context-aware capabilities"""
    logger.info(f"Processing enhanced query: {query_request.question[:50]}...")
    
    try:
        service = QueryService(db)
        
        # Use the enhanced context-aware processing
        result = await service.process_context_aware_query(
            question=query_request.question,
            dataset_id=query_request.dataset_id,
            session_id=query_request.session_id,
            workspace_id=query_request.workspace_id,
            auto_select=query_request.auto_select,
            max_datasets=query_request.max_datasets,
            context_hint=query_request.context_hint,
            profile_name=query_request.profile_name
        )
        
        logger.info("Enhanced query processed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error processing enhanced query: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to process enhanced query",
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

@query_router.post("/analyze-intent/", response_model=Dict[str, Any])
async def analyze_query_intent(
    request: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Analyze query intent and scope using QueryIntentAnalyzer"""
    question = request.get("question", "")
    if not question:
        return ResponseHandler.create_error_response(
            error="Missing question",
            message="Question is required",
            response_type=ResponseType.VALIDATION_ERROR
        )
    
    logger.info(f"Analyzing intent for question: {question[:50]}...")
    
    try:
        analyzer = QueryIntentAnalyzer()
        analysis = analyzer.analyze_complete_query(question)
        
        return ResponseHandler.create_success_response(
            data=analysis,
            message="Query intent analyzed successfully",
            response_type=ResponseType.GENERAL
        )
        
    except Exception as e:
        logger.error(f"Error analyzing query intent: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to analyze query intent",
            response_type=ResponseType.GENERAL
        )

@query_router.post("/smart-query/", response_model=Dict[str, Any])
async def smart_query_processing(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Smart query processing with full auto-detection: datasets + agents + context"""
    logger.info("Processing smart query with full auto-detection")
    
    try:
        question = request.get("question", "")
        if not question:
            return ResponseHandler.create_error_response(
                error="Missing question",
                message="Question is required",
                response_type=ResponseType.VALIDATION_ERROR
            )
        
        service = QueryService(db)
        
        # Step 1: Analyze query intent
        logger.info("Step 1: Analyzing query intent...")
        intent_analysis = service.intent_analyzer.analyze_complete_query(question)
        
        # Step 2: Auto-select datasets
        logger.info("Step 2: Auto-selecting relevant datasets...")
        from app.services.dataset_service import DatasetService
        dataset_service = DatasetService(db)
        
        datasets_response = await dataset_service.get_all_datasets()
        if not ResponseHandler.is_success(datasets_response):
            return ResponseHandler.create_error_response(
                error="Failed to get datasets",
                message="Could not retrieve available datasets",
                response_type=ResponseType.VALIDATION_ERROR
            )
        
        datasets_data = ResponseHandler.extract_data_safely(datasets_response)
        available_dataset_ids = [d["id"] for d in datasets_data]
        
        if not available_dataset_ids:
            return ResponseHandler.create_error_response(
                error="No datasets available",
                message="No datasets available for processing",
                response_type=ResponseType.VALIDATION_ERROR
            )
        
        selection_result = await service.selection_service.auto_select_datasets(
            question=question,
            available_datasets=available_dataset_ids,
            max_datasets=3
        )
        
        if not ResponseHandler.is_success(selection_result):
            return selection_result
        
        selection_data = ResponseHandler.extract_data_safely(selection_result)
        selected_datasets = selection_data.get("selected_datasets", [])
        
        if not selected_datasets:
            return ResponseHandler.create_error_response(
                error="No suitable datasets found",
                message="No datasets match the query requirements",
                response_type=ResponseType.VALIDATION_ERROR
            )
        
        # Step 3: Auto-select agent profile
        logger.info("Step 3: Auto-selecting agent profile...")
        recommendations = intent_analysis['processing_recommendations']
        agent_profile = recommendations.get('agent_profile', 'general_analyst')
        
        # Step 4: Process query with auto-selected dataset and agent
        logger.info(f"Step 4: Processing query with dataset {selected_datasets[0]} and agent {agent_profile}")
        
        query_result = await service.process_natural_language_query(
            question=question,
            dataset_id=selected_datasets[0],
            session_id=str(uuid.uuid4()),
            profile_name=agent_profile
        )
        
        # Step 5: Enhance response with auto-detection metadata
        if ResponseHandler.is_success(query_result):
            result_data = ResponseHandler.extract_data_safely(query_result)
            
            enhanced_response = {
                **result_data,
                "auto_detection_metadata": {
                    "intent_analysis": intent_analysis,
                    "dataset_selection": selection_data,
                    "selected_datasets": selected_datasets,
                    "selected_agent": agent_profile,
                    "mode": "full_auto_detection",
                    "confidence": {
                        "dataset_selection": max([score for score in selection_data.get("all_scores", {}).values()]),
                        "agent_selection": recommendations.get('confidence', 0.5)
                    }
                }
            }
            
            return ResponseHandler.create_success_response(
                data=enhanced_response,
                message="Smart query processed successfully with full auto-detection",
                response_type=ResponseType.QUERY_RESULT
            )
        else:
            return query_result
        
    except Exception as e:
        logger.error(f"Error in smart query processing: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to process smart query",
            response_type=ResponseType.QUERY_RESULT
        )