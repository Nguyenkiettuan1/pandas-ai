from typing import Optional, List, Any, Dict
import pandas as pd
from pandasai import Agent
from pandasai.llm import OpenAI
from pandasai.connectors import PostgreSQLConnector
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging_config import get_logger
from app.models import Dataset, Query
from app.agents.profile_manager import profile_manager
from app.agents.tools import (
    DataDescriptionTool, DataFilterTool, DataAggregationTool,
    SalesSummaryTool, CustomerAnalysisTool, PerformanceMetricsTool
)
import time
import json
import traceback

logger = get_logger(__name__)

class PandasAIAgent:
    def __init__(self, db: Session):
        self.db = db
        self.llm = OpenAI(api_token=settings.OPENAI_API_KEY)
        self.agents = {}  # Cache for dataset agents
        self.tools = self._initialize_tools()
        logger.info("PandasAI Agent initialized")
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize available tools"""
        tools = {
            "describe_data": DataDescriptionTool(),
            "filter_data": DataFilterTool(),
            "aggregate_data": DataAggregationTool(),
            "sales_summary": SalesSummaryTool(),
            "customer_analysis": CustomerAnalysisTool(),
            "performance_metrics": PerformanceMetricsTool()
        }
        logger.debug(f"Initialized {len(tools)} tools: {list(tools.keys())}")
        return tools
    def get_or_create_agent(self, dataset_id: int, profile_name: str = "general_analyst") -> Agent:
        """Get or create a PandasAI agent for a specific dataset with profile"""
        cache_key = f"{dataset_id}_{profile_name}"
        
        if cache_key in self.agents:
            logger.debug(f"Using cached agent for dataset {dataset_id} with profile {profile_name}")
            return self.agents[cache_key]
        
        logger.info(f"Creating new agent for dataset {dataset_id} with profile {profile_name}")
        
        # Get dataset information
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            logger.error(f"Dataset with id {dataset_id} not found")
            raise ValueError(f"Dataset with id {dataset_id} not found")
        
        # Load agent profile
        profile = profile_manager.get_profile(profile_name)
        if not profile:
            logger.warning(f"Profile {profile_name} not found, using default configuration")
            profile = profile_manager.get_profile("general_analyst")
        
        logger.info(f"Using profile: {profile.name} v{profile.version}")
        
        try:
            # Create PostgreSQL connector
            connector = PostgreSQLConnector(
                config={
                    "host": settings.DB_HOST,
                    "port": settings.DB_PORT,
                    "database": settings.DB_NAME,
                    "username": settings.DB_USER,
                    "password": settings.DB_PASSWORD,
                    "table": dataset.table_name
                }
            )
            
            # Configure LLM based on profile
            llm_config = profile.config if profile else {}
            configured_llm = OpenAI(
                api_token=settings.OPENAI_API_KEY,
                model=llm_config.get("llm_model", "gpt-3.5-turbo"),
                temperature=llm_config.get("temperature", 0.1),
                max_tokens=llm_config.get("max_tokens", 2000)
            )
            
            # Create and cache agent
            agent = Agent([connector], config={"llm": configured_llm})
            self.agents[cache_key] = agent
            
            logger.info(f"Successfully created agent for dataset {dataset.name}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent for dataset {dataset_id}: {e}")
            logger.error(traceback.format_exc())
            raise
    async def process_question(
        self, 
        question: str, 
        dataset_id: int, 
        session_id: Optional[str] = None,
        profile_name: str = "general_analyst"
    ) -> Dict[str, Any]:
        """Process a natural language question against a dataset"""
        logger.info(f"Processing question for dataset {dataset_id}: {question[:100]}...")
        
        try:
            start_time = time.time()
            
            # Get the agent for this dataset with specified profile
            agent = self.get_or_create_agent(dataset_id, profile_name)
            
            # Get profile for context
            profile = profile_manager.get_profile(profile_name)
            
            logger.debug(f"Using profile: {profile.name if profile else 'default'}")
            
            # Process the question with enhanced context
            enhanced_question = self._enhance_question_with_profile(question, profile)
            
            logger.debug(f"Enhanced question: {enhanced_question}")
            
            # Process the question
            result = agent.chat(enhanced_question)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"Question processed successfully in {execution_time}ms")
            
            # Save query to database
            query = Query(
                question=question,
                result=str(result),
                execution_time=execution_time,
                dataset_id=dataset_id
            )
            self.db.add(query)
            self.db.commit()
            self.db.refresh(query)
            
            response = {
                "query_id": query.id,
                "question": question,
                "result": result,
                "execution_time": execution_time,
                "dataset_id": dataset_id,
                "profile_used": profile_name,
                "session_id": session_id
            }
            
            logger.debug(f"Response prepared: {type(result)}")
            return response
            
        except Exception as e:
            error_msg = str(e)
            execution_time = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
            
            logger.error(f"Error processing question: {error_msg}")
            logger.error(traceback.format_exc())
            
            # Log error and save failed query
            query = Query(
                question=question,
                result=f"Error: {error_msg}",
                execution_time=execution_time,
                dataset_id=dataset_id
            )
            self.db.add(query)
            self.db.commit()
            
            raise Exception(f"Failed to process question: {error_msg}")
    
    def _enhance_question_with_profile(self, question: str, profile) -> str:
        """Enhance question with profile-specific context"""
        if not profile:
            return question
        
        # Add domain-specific context
        enhanced = question
        
        if hasattr(profile, 'domain_knowledge') and profile.domain_knowledge:
            if 'business_terms' in profile.domain_knowledge:
                enhanced += f"\n\nConsider these business terms: {', '.join(profile.domain_knowledge['business_terms'])}"
        
        if hasattr(profile, 'capabilities') and profile.capabilities:
            enhanced += f"\n\nAvailable capabilities: {', '.join(profile.capabilities)}"
        
        return enhanced
    
    async def get_query_history(self, dataset_id: int, limit: int = 10) -> List[Dict]:
        """Get query history for a dataset"""
        queries = (
            self.db.query(Query)
            .filter(Query.dataset_id == dataset_id)
            .order_by(Query.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "id": q.id,
                "question": q.question,
                "result": q.result,
                "execution_time": q.execution_time,
                "created_at": q.created_at
            }
            for q in queries
        ]
    
    def clear_agent_cache(self, dataset_id: Optional[int] = None):
        """Clear agent cache for specific dataset or all datasets"""
        if dataset_id:
            self.agents.pop(dataset_id, None)
        else:
            self.agents.clear()
