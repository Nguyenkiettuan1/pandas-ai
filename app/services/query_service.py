from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.query import Query
from app.models.dataset import Dataset  # Add this import
from app.agents.pandas_agent import PandasAIAgent
from app.agents.agent_router import agent_router  # Add agent router
from app.core.logging_config import get_logger
from app.core.response_handler import ResponseHandler, ResponseType
from app.services.context_service import ContextService  # Add context service
from app.services.dataset_selection_service import DatasetSelectionService  # Add selection service
import pandas as pd
import time

logger = get_logger(__name__)

class QueryService:
    def __init__(self, db: Session):
        self.db = db
        self.pandas_agent = PandasAIAgent(db)
        self.context_service = ContextService(db)  # Add context service
        self.selection_service = DatasetSelectionService(db)  # Add selection service
        logger.debug("QueryService initialized with context support")

    async def process_context_aware_query(
        self,
        question: str,
        dataset_id: Optional[int] = None,
        session_id: Optional[Union[str, UUID]] = None,
        workspace_id: Optional[Union[str, UUID]] = None,
        auto_select: bool = True,
        max_datasets: int = 3,
        context_hint: Optional[str] = None,
        profile_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query with flexible context support
        
        Args:
            question: Natural language question
            dataset_id: Explicit dataset ID (legacy mode)
            session_id: Session context for dataset selection
            workspace_id: Workspace context for dataset selection
            auto_select: Enable automatic dataset selection
            max_datasets: Maximum datasets to use in auto-selection
            context_hint: Hint for dataset selection
            profile_name: Agent profile to use
            
        Returns:
            Enhanced query response with context information
        """
        start_time = time.time()
        logger.info(f"Processing context-aware query: '{question[:50]}...'")
        
        try:
            # Step 1: Resolve query context and get available datasets
            context_resolution_start = time.time()
            
            if dataset_id:
                # Legacy mode - explicit dataset
                context_info = {
                    "strategy": "explicit",
                    "available_datasets": [dataset_id],
                    "default_dataset": dataset_id,
                    "context_metadata": {}
                }
                context_type = "explicit"
            else:
                # Context-aware mode
                context_response = await self.context_service.resolve_query_context(
                    session_id=session_id,
                    workspace_id=workspace_id,
                    dataset_id=dataset_id
                )
                
                if not ResponseHandler.is_success(context_response):
                    return context_response
                
                context_info = ResponseHandler.extract_data_safely(context_response)
                
                if session_id:
                    context_type = "session"
                elif workspace_id:
                    context_type = "workspace"
                else:
                    context_type = "auto"
            
            context_resolution_time = time.time() - context_resolution_start
            
            # Step 2: Auto-select datasets if needed and enabled
            available_datasets = context_info.get("available_datasets", [])
            
            if not available_datasets and auto_select:
                # No context provided, try to find all available datasets
                all_datasets = self.db.query(Dataset).filter(Dataset.is_active == True).all()
                available_datasets = [d.id for d in all_datasets]
                context_info["strategy"] = "auto_discovery"
                context_type = "auto_discovery"
            
            if not available_datasets:
                return ResponseHandler.create_error_response(
                    error="No datasets available",
                    message="No datasets available for query processing",
                    response_type=ResponseType.VALIDATION_ERROR
                )
            
            # Step 3: Intelligent dataset selection (if multiple datasets available)
            selected_datasets = available_datasets
            dataset_selection_metadata = None
            
            if len(available_datasets) > 1 and auto_select:
                selection_response = await self.selection_service.auto_select_datasets(
                    question=question,
                    available_datasets=available_datasets,
                    max_datasets=max_datasets,
                    context_hint=context_hint
                )
                
                if ResponseHandler.is_success(selection_response):
                    selection_data = ResponseHandler.extract_data_safely(selection_response)
                    selected_datasets = selection_data.get("selected_datasets", available_datasets[:max_datasets])
                    dataset_selection_metadata = selection_data.get("selection_metadata")
                    logger.info(f"Auto-selected {len(selected_datasets)} datasets: {selected_datasets}")
                else:
                    # Fallback to using default dataset or first few available
                    default_dataset = context_info.get("default_dataset")
                    if default_dataset and default_dataset in available_datasets:
                        selected_datasets = [default_dataset]
                    else:
                        selected_datasets = available_datasets[:max_datasets]
                    logger.warning("Dataset auto-selection failed, using fallback selection")
            
            # Step 4: Auto-route to appropriate agent profile if not specified
            if not profile_name:
                # Use existing validation logic to determine profile
                validation_result = await self.validate_query_parameters(
                    question=question,
                    dataset_id=selected_datasets[0],  # Use first selected dataset for routing
                    profile_name=None
                )
                
                if ResponseHandler.is_success(validation_result):
                    validated_data = ResponseHandler.extract_data_safely(validation_result)
                    profile_name = validated_data.get("validated_profile", "general_analyst")
                else:
                    profile_name = "general_analyst"
            
            # Step 5: Process the query
            # For now, use the first selected dataset (can be enhanced for multi-dataset queries)
            primary_dataset_id = selected_datasets[0]
            
            query_result = await self.process_natural_language_query(
                question=question,
                dataset_id=primary_dataset_id,
                session_id=str(session_id) if session_id else None,
                profile_name=profile_name
            )
            
            # Step 6: Enhance response with context information
            if ResponseHandler.is_success(query_result):
                result_data = ResponseHandler.extract_data_safely(query_result)
                
                # Add context information to the response
                enhanced_data = {
                    **result_data,
                    "context_type": context_type,
                    "session_id": session_id,
                    "workspace_id": workspace_id,
                    "dataset_selection": dataset_selection_metadata.dict() if dataset_selection_metadata else None,
                    "selected_datasets": selected_datasets,
                    "available_datasets": available_datasets,
                    "context_resolution_time": context_resolution_time,
                    "total_execution_time": time.time() - start_time
                }
                
                return ResponseHandler.create_success_response(
                    data=enhanced_data,
                    message=f"Query processed successfully using {context_type} context",
                    response_type=ResponseType.QUERY_RESULT
                )
            else:
                return query_result
                
        except Exception as e:
            logger.error(f"Error in context-aware query processing: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to process context-aware query",
                response_type=ResponseType.QUERY_RESULT
            )
        
    async def process_natural_language_query(
        self, 
        question: str, 
        dataset_id: int,
        session_id: str = None,
        profile_name: str = "general_analyst"
    ) -> Dict[str, Any]:
        """Process a natural language query using PandasAI with specified profile"""
        logger.info(f"Processing query for dataset {dataset_id} with profile {profile_name}")
        
        start_time = time.time()
        
        try:
            result = await self.pandas_agent.process_question(
                question=question,
                dataset_id=dataset_id,
                session_id=session_id,
                profile_name=profile_name
            )
            
            execution_time = time.time() - start_time
            
            return ResponseHandler.create_query_response(
                result=result,
                execution_time=execution_time,
                query=question,
                dataset_id=dataset_id,
                profile_name=profile_name,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error processing query: {e}")
            return ResponseHandler.create_query_response(
                result=None,
                execution_time=execution_time,
                query=question,
                dataset_id=dataset_id,
                profile_name=profile_name,
                success=False,
                error=str(e)
            )
    
    async def get_query_history(
        self, 
        dataset_id: int = None, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get query history"""
        logger.debug(f"Getting query history for dataset {dataset_id}, limit {limit}")
        
        try:
            query = self.db.query(Query)
            
            if dataset_id:
                query = query.filter(Query.dataset_id == dataset_id)
            
            queries = query.order_by(Query.created_at.desc()).limit(limit).all()
            
            logger.info(f"Retrieved {len(queries)} query records")
            query_data = [
                {
                    "id": q.id,
                    "question": q.question,
                    "result": q.result,
                    "execution_time": q.execution_time,
                    "dataset_id": q.dataset_id,
                    "created_at": q.created_at
                }
                for q in queries
            ]
            
            return ResponseHandler.create_history_response(
                queries=query_data,
                dataset_id=dataset_id,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error retrieving query history: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to retrieve query history",
                response_type=ResponseType.QUERY_HISTORY
            )
    
    async def get_dataset_insights(self, dataset_id: int, profile_name: str = "general_analyst") -> Dict[str, Any]:
        """Get automated insights for a dataset"""
        logger.info(f"Getting insights for dataset {dataset_id} with profile {profile_name}")
        
        try:
            insights = await self.pandas_agent.get_dataset_insights(dataset_id, profile_name)
            
            return ResponseHandler.create_dataset_insights_response(
                insights=insights,
                dataset_id=dataset_id,
                profile_name=profile_name,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error getting dataset insights: {e}")
            return ResponseHandler.create_dataset_insights_response(
                insights=None,
                dataset_id=dataset_id,
                profile_name=profile_name,
                success=False,
                error=str(e)
            )
    
    async def execute_tool(self, tool_name: str, dataset_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool on a dataset"""
        logger.info(f"Executing tool {tool_name} on dataset {dataset_id}")
        
        start_time = time.time()
        
        try:
            # For this implementation, we'd need to load the dataset data
            # and pass it to the tool execution method
            
            # Placeholder - in production, load actual data
            data = pd.DataFrame()
            
            result = await self.pandas_agent.execute_tool(tool_name, data, parameters)
            execution_time = time.time() - start_time
            
            return ResponseHandler.create_tool_execution_response(
                result=result,
                tool_name=tool_name,
                dataset_id=dataset_id,
                parameters=parameters,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing tool {tool_name}: {e}")
            
            error_result = {"success": False, "error": str(e)}
            return ResponseHandler.create_tool_execution_response(
                result=error_result,
                tool_name=tool_name,
                dataset_id=dataset_id,
                parameters=parameters,
                execution_time=execution_time
            )
    
    async def get_agent_suggestions(self, question: str, dataset_id: int) -> Dict[str, Any]:
        """Get agent suggestions for a question using agent router"""
        logger.info(f"Getting agent suggestions for question: {question[:50]}...")
        
        try:
            # Get dataset context
            dataset = await self.get_dataset_by_id(dataset_id)
            if not dataset:
                return ResponseHandler.create_error_response(
                    error=ValueError(f"Dataset {dataset_id} not found"),
                    message="Dataset not found",
                    response_type=ResponseType.VALIDATION_ERROR
                )
            
            dataset_context = {
                'table_name': dataset.get('table_name', ''),
                'dataset_name': dataset.get('name', ''),
                'description': dataset.get('description', '')
            }
            
            # Get suggestions from agent router
            suggestions = agent_router.get_agent_suggestions(question, top_n=5)
            recommended = agent_router.route_question(question, dataset_context)
            
            response_data = {
                "question": question,
                "dataset_id": dataset_id,
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
    
    async def get_dataset_by_id(self, dataset_id: int) -> Dict[str, Any]:
        """Get dataset information by ID"""
        try:
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return None
            
            return {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "table_name": dataset.table_name,
                "created_at": dataset.created_at
            }
        except Exception as e:
            logger.error(f"Error getting dataset {dataset_id}: {e}")
            return None
    
    async def validate_query_parameters(
        self, 
        question: str, 
        dataset_id: int, 
        profile_name: str = None
    ) -> Dict[str, Any]:
        """Validate query parameters and suggest appropriate agent profile"""
        try:
            # Validate dataset exists
            dataset = await self.get_dataset_by_id(dataset_id)
            if not dataset:
                return ResponseHandler.create_error_response(
                    error=ValueError(f"Dataset {dataset_id} not found"),
                    message="Dataset not found",
                    response_type=ResponseType.VALIDATION_ERROR
                )
            
            # Remember if we're auto-routing
            is_auto_routed = profile_name is None
            
            # If no profile specified, auto-route
            if not profile_name:
                dataset_context = {
                    'table_name': dataset.get('table_name', ''),
                    'dataset_name': dataset.get('name', ''),
                    'description': dataset.get('description', '')
                }
                
                suggested_agent = agent_router.route_question(question, dataset_context)
                profile_name = suggested_agent.value
                logger.info(f"Auto-routed to agent: {profile_name}")
            
            validation_result = {
                "validated_profile": profile_name,
                "dataset_info": dataset,
                "is_auto_routed": is_auto_routed
            }
            
            return ResponseHandler.create_success_response(
                data=validation_result,
                message="Parameters validated successfully",
                response_type=ResponseType.VALIDATION_SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Error validating parameters: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Parameter validation failed",
                response_type=ResponseType.VALIDATION_ERROR
            )
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            health_data = {
                "service_name": "QueryService",
                "database_connected": self.db is not None,
                "pandas_agent_initialized": self.pandas_agent is not None,
                "timestamp": time.time()
            }
            
            # Test database connection
            try:
                self.db.execute("SELECT 1")
                health_data["database_status"] = "healthy"
            except Exception as db_error:
                health_data["database_status"] = "unhealthy"
                health_data["database_error"] = str(db_error)
            
            return ResponseHandler.create_success_response(
                data=health_data,
                message="Service health check completed",
                response_type=ResponseType.GENERAL
            )
            
        except Exception as e:
            logger.error(f"Error checking service health: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Health check failed",
                response_type=ResponseType.GENERAL
            )
    
    async def get_query_statistics(self, dataset_id: int = None) -> Dict[str, Any]:
        """Get statistics about queries"""
        try:
            query = self.db.query(Query)
            
            if dataset_id:
                query = query.filter(Query.dataset_id == dataset_id)
            
            total_queries = query.count()
            
            if total_queries == 0:
                stats = {
                    "total_queries": 0,
                    "dataset_id": dataset_id,
                    "message": "No queries found"
                }
            else:
                # Calculate statistics
                execution_times = [q.execution_time for q in query.all() if q.execution_time]
                
                stats = {
                    "total_queries": total_queries,
                    "dataset_id": dataset_id,
                    "execution_stats": {
                        "average_time": sum(execution_times) / len(execution_times) if execution_times else 0,
                        "min_time": min(execution_times) if execution_times else 0,
                        "max_time": max(execution_times) if execution_times else 0,
                        "total_time": sum(execution_times) if execution_times else 0
                    },
                    "query_count_by_dataset": {}
                }
                
                # Get query counts by dataset
                if not dataset_id:
                    dataset_counts = self.db.query(Query.dataset_id, self.db.func.count(Query.id)).group_by(Query.dataset_id).all()
                    stats["query_count_by_dataset"] = {str(ds_id): count for ds_id, count in dataset_counts}
            
            return ResponseHandler.create_success_response(
                data=stats,
                message="Query statistics retrieved successfully",
                response_type=ResponseType.GENERAL
            )
            
        except Exception as e:
            logger.error(f"Error getting query statistics: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to retrieve query statistics",
                response_type=ResponseType.GENERAL
            )
