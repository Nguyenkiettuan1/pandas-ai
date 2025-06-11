from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.query import Query
from app.models.dataset import Dataset  # Add this import
from app.agents.pandas_agent import PandasAIAgent
from app.core.logging_config import get_logger
from app.core.response_handler import ResponseHandler, ResponseType
import pandas as pd
import time

logger = get_logger(__name__)

class QueryService:
    def __init__(self, db: Session):
        self.db = db
        self.pandas_agent = PandasAIAgent(db)
        logger.debug("QueryService initialized")
        
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
                    "execution_time": q.execution_time,                "dataset_id": q.dataset_id,
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
    
    async def validate_query_parameters(
        self, 
        question: str, 
        dataset_id: int, 
        profile_name: str
    ) -> Dict[str, Any]:
        """Validate query parameters before processing"""
        try:
            errors = []
            warnings = []
            
            # Validate question
            if not question or not question.strip():
                errors.append("Question cannot be empty")
            elif len(question.strip()) < 5:
                warnings.append("Question is very short - consider providing more detail")
            
            # Validate dataset_id
            if not isinstance(dataset_id, int) or dataset_id <= 0:
                errors.append("Dataset ID must be a positive integer")
            
            # Validate profile_name
            valid_profiles = ["general_analyst", "sales_specialist", "marketing_analyst", "financial_expert"]
            if profile_name not in valid_profiles:
                warnings.append(f"Profile '{profile_name}' not recognized. Using 'general_analyst'")
                profile_name = "general_analyst"
            
            if errors:
                return ResponseHandler.create_error_response(
                    error="; ".join(errors),
                    message="Parameter validation failed",
                    response_type=ResponseType.VALIDATION
                )
            elif warnings:
                return ResponseHandler.create_warning_response(
                    data={"validated_profile": profile_name},
                    message="Parameters validated with warnings",
                    warnings=warnings,
                    response_type=ResponseType.VALIDATION
                )
            else:
                return ResponseHandler.create_success_response(
                    data={"validated_profile": profile_name},
                    message="All parameters validated successfully",
                    response_type=ResponseType.VALIDATION
                )
                
        except Exception as e:
            logger.error(f"Error validating parameters: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Validation process failed",
                response_type=ResponseType.VALIDATION
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
