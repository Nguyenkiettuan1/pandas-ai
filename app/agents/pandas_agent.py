from typing import Optional, List, Any, Dict
import pandas as pd
from pandasai import Agent
from pandasai.llm import OpenAI, BambooLLM
from pandasai.connectors import PostgreSQLConnector
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.core.config import settings
from app.core.logging_config import get_logger
from app.models import Dataset, Query
from app.agents.profile_manager import profile_manager
from app.agents.llm_factory import llm_factory
from app.agents.tools import (
    DataDescriptionTool, DataFilterTool, DataAggregationTool,
    SalesSummaryTool, CustomerAnalysisTool, PerformanceMetricsTool
)
import time
import json
import traceback
from app.agents.smart_fallback_agent import SmartFallbackAgent
from app.agents.agent_router import agent_router, AgentType

logger = get_logger(__name__)

class PandasAIAgent:
    def __init__(self, db: Session):
        self.db = db
        self.agents = {}  # Cache for dataset agents
        self.tools = self._initialize_tools()
        logger.info("PandasAI Agent initialized")
        
    def _create_llm_for_profile(self, profile_config: Dict[str, Any] = None):
        """Create LLM using factory with profile configuration"""
        return llm_factory.create_llm(profile_config)
    
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
          # Load agent profile and get LLM config from YAML
        profile = profile_manager.get_profile(profile_name)
        if not profile:
            logger.warning(f"Profile {profile_name} not found, using default configuration")
            profile = profile_manager.get_profile("general_analyst")
        
        logger.info(f"Using profile: {profile.name} v{profile.version}")
        
        # Create LLM based on profile configuration from YAML
        llm_config = profile.config if profile else {}
        configured_llm = self._create_llm_for_profile(llm_config)
        
        # Try pandas DataFrame approach first (more reliable)
        try:
            logger.info("Creating agent with pandas DataFrame approach...")
            
            # Create SQLAlchemy engine and load data directly
            engine = create_engine(settings.DATABASE_URL)
            df = pd.read_sql_table(dataset.table_name, engine)
            logger.info(f"Loaded DataFrame with shape: {df.shape}")
            logger.info(f"DataFrame columns: {list(df.columns)}")
            logger.info(f"DataFrame head:\n{df.head(2)}")
              # Create agent with DataFrame - this is more reliable than PostgreSQL connector
            agent_config = {
                "llm": configured_llm,
                "verbose": True,
                "enforce_privacy": False,
                "enable_cache": False,  # Disable cache for debugging
                "conversational": False,
                "save_logs": True,
                "custom_whitelisted_dependencies": ["pandas", "numpy", "matplotlib", "seaborn"],
                "enable_vectorstore": False,  # Disable vectorstore to avoid API key issues
                "direct_sql": False
            }
            
            logger.debug(f"Creating agent with DataFrame, config: {agent_config}")
            agent = Agent(df, config=agent_config)
            self.agents[cache_key] = agent
            
            logger.info(f"Successfully created DataFrame agent for dataset {dataset.name}")
            return agent
            
        except Exception as df_error:
            logger.error(f"DataFrame approach failed: {df_error}")
            
            # Fallback to PostgreSQL connector
            try:
                logger.info("Trying fallback with PostgreSQL connector...")
                
                # Create PostgreSQL connector with better error handling
                connector_config = {
                    "host": settings.DB_HOST,
                    "port": settings.DB_PORT,
                    "database": settings.DB_NAME,
                    "username": settings.DB_USER,
                    "password": settings.DB_PASSWORD,
                    "table": dataset.table_name,
                    "schema": "public"
                }
                
                logger.debug(f"Creating connector with config: {connector_config}")
                connector = PostgreSQLConnector(config=connector_config)
                
                # Test connector by loading a sample
                try:
                    sample_data = connector.head()
                    logger.info(f"Connector test successful, sample data shape: {sample_data.shape}")
                except Exception as conn_error:
                    logger.error(f"Connector test failed: {conn_error}")
                    raise Exception(f"Failed to connect to table {dataset.table_name}: {conn_error}")
                  # Create agent with connector
                agent_config = {
                    "llm": configured_llm,
                    "verbose": True,
                    "enforce_privacy": False,
                    "enable_cache": False,
                    "conversational": False,
                    "save_logs": True,
                    "custom_whitelisted_dependencies": ["pandas", "numpy", "matplotlib", "seaborn"],
                    "enable_vectorstore": False,  # Disable vectorstore to avoid API key issues
                    "direct_sql": False
                }
                
                logger.debug(f"Creating agent with connector, config: {agent_config}")
                agent = Agent([connector], config=agent_config)
                self.agents[cache_key] = agent
                
                logger.info(f"Successfully created connector agent for dataset {dataset.name}")
                return agent
                
            except Exception as connector_error:
                logger.error(f"Both DataFrame and PostgreSQL connector failed")
                logger.error(f"DataFrame error: {df_error}")
                logger.error(f"Connector error: {connector_error}")
                raise Exception(f"Failed to create agent for dataset {dataset_id}: {connector_error}")
    
    async def process_question(
        self, 
        question: str, 
        dataset_id: int, 
        session_id: Optional[str] = None,
        profile_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a natural language question against a dataset"""
        logger.info(f"Processing question for dataset {dataset_id}: {question[:100]}...")
        try:
            start_time = time.time()
            
            # Track original profile name to determine if auto-routing occurred
            original_profile_name = profile_name
            
            # Get dataset information for context
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise ValueError(f"Dataset with id {dataset_id} not found")
            
            # Auto-route to appropriate agent if profile not specified
            if not profile_name:
                dataset_context = {
                    'table_name': dataset.table_name,
                    'dataset_name': dataset.name,
                    'description': dataset.description
                }
                
                suggested_agent = agent_router.route_question(question, dataset_context)
                profile_name = suggested_agent.value
                logger.info(f"Auto-routed to agent: {profile_name}")
            
            # Get the agent for this dataset with specified/routed profile
            agent = self.get_or_create_agent(dataset_id, profile_name)
            
            # Get profile for context
            profile = profile_manager.get_profile(profile_name)
            
            logger.debug(f"Using profile: {profile.name if profile else 'default'}")
              # Process the question with enhanced context
            enhanced_question = self._enhance_question_with_profile(question, profile)
            
            logger.debug(f"Enhanced question: {enhanced_question}")
            
            # Create enhanced prompt for better natural language + statistical analysis
            enhanced_prompt = self._create_enhanced_prompt(enhanced_question, dataset, profile)
            
            logger.debug(f"Enhanced prompt created: {len(enhanced_prompt)} chars")
              # Process the question with better error handling
            try:
                # Use enhanced prompt instead of simple contextual question
                result = agent.chat(enhanced_prompt)
                logger.info(f"Agent response type: {type(result)}")
                logger.debug(f"Agent raw result: {str(result)[:200]}...")
                
                # Check if result contains error patterns
                if isinstance(result, str):
                    error_patterns = ["'data'", "error", "failed", "cannot", "unable"]
                    if any(pattern in result.lower() for pattern in error_patterns):
                        logger.warning("PandasAI returned error-like result, trying fallback...")
                        raise Exception("PandasAI returned error result")
                
            except Exception as agent_error:
                logger.error(f"PandasAI agent error: {agent_error}")
                  # Try with a simpler question format
                try:
                    simple_question = question.strip()
                    logger.info(f"Trying with simpler question: {simple_question}")
                    result = agent.chat(simple_question)
                    
                    if isinstance(result, str) and any(pattern in result.lower() for pattern in ["'data'", "error"]):
                        raise Exception("Simple question also failed")
                        
                except Exception as simple_error:
                    logger.error(f"Simple question also failed: {simple_error}")
                    
                    # Try smart fallback agent as final option
                    fallback_result = await self._try_smart_fallback(question, dataset_id)
                    if fallback_result:
                        result = fallback_result
                    else:
                        # Try with different agents as last resort
                        fallback_result = await self._try_fallback_agents(
                            question, dataset_id, profile_name, agent_error
                        )
                        if fallback_result:
                            result = fallback_result
                        else:
                            result = f"Sorry, I couldn't process your question. Error: {str(agent_error)}"
            execution_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"Question processed successfully in {execution_time}ms")
            
            # Convert result to serializable format
            serializable_result = self._convert_result_to_serializable(result)
            
            # Save query to database
            query = Query(
                question=question,
                result=serializable_result,
                execution_time=execution_time,
                dataset_id=dataset_id
            )
            self.db.add(query)
            self.db.commit()
            self.db.refresh(query)
              # Determine if it was auto-routed (profile_name was not provided initially)
            was_auto_routed = original_profile_name is None
            
            response = {
                "query_id": query.id,
                "question": question,
                "result": serializable_result,
                "execution_time": execution_time,
                "dataset_id": dataset_id,
                "profile_used": profile_name,
                "session_id": session_id,
                "auto_routed": was_auto_routed
            }
            
            logger.debug(f"Response prepared with result type: {type(serializable_result)}")
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
    
    async def _try_fallback_agents(
        self, 
        question: str, 
        dataset_id: int, 
        failed_profile: str, 
        original_error: Exception
    ) -> Optional[str]:
        """Try fallback agents when primary agent fails"""
        logger.info("Trying fallback agents...")
        
        # Get suggestions excluding the failed one
        suggestions = agent_router.get_agent_suggestions(question, top_n=3)
        fallback_profiles = [s['agent'] for s in suggestions if s['agent'] != failed_profile]
        
        for fallback_profile in fallback_profiles[:2]:  # Try top 2 alternatives
            try:
                logger.info(f"Trying fallback agent: {fallback_profile}")
                fallback_agent = self.get_or_create_agent(dataset_id, fallback_profile)
                result = fallback_agent.chat(question)
                
                if result and not (isinstance(result, str) and "'data'" in result.lower()):
                    logger.info(f"Fallback agent {fallback_profile} succeeded")
                    return f"[Used {fallback_profile} agent] {result}"
                    
            except Exception as fallback_error:
                logger.warning(f"Fallback agent {fallback_profile} also failed: {fallback_error}")
                continue
        
        return None
    
    async def _try_smart_fallback(self, question: str, dataset_id: int) -> Optional[str]:
        """Try smart fallback agent for common queries"""
        try:
            logger.info("Trying smart fallback agent...")
            
            # Get dataset and load data for fallback agent
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return None
            
            # Load data using SQLAlchemy
            from sqlalchemy import create_engine
            engine = create_engine(settings.DATABASE_URL)
            df = pd.read_sql_table(dataset.table_name, engine)
            
            # Create smart fallback agent
            fallback_agent = SmartFallbackAgent(df)
            
            # Try to process with fallback
            result = fallback_agent.process_question(question)
            
            if result:
                logger.info("Smart fallback agent succeeded")
                return result
            
            return None
            
        except Exception as e:
            logger.warning(f"Smart fallback agent failed: {e}")
            return None
    
    async def get_agent_suggestions(self, question: str, dataset_id: int) -> Dict[str, Any]:
        """Get agent suggestions for a question"""
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")
        
        dataset_context = {
            'table_name': dataset.table_name,
            'dataset_name': dataset.name,
            'description': dataset.description
        }
        
        suggestions = agent_router.get_agent_suggestions(question, top_n=5)
        recommended = agent_router.route_question(question, dataset_context)
        
        return {
            "question": question,
            "recommended_agent": recommended.value,
            "all_suggestions": suggestions,            "dataset_context": dataset_context
        }
    
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
    
    def _create_enhanced_prompt(self, question: str, dataset, profile) -> str:
        """Create enhanced prompt for natural language + statistical analysis"""
        
        # Base prompt template for Vietnamese/English natural language + statistics
        base_prompt = f"""
        Bạn là một chuyên gia phân tích dữ liệu thông minh, có khả năng xử lý cả câu hỏi bằng tiếng Việt và tiếng Anh.
        Bạn có thể trả lời cả câu hỏi natural language và tính toán thống kê phức tạp.

        DATASET CONTEXT:
        - Tên dataset: {dataset.name}
        - Tên bảng: {dataset.table_name}
        - Mô tả: {dataset.description or 'Không có mô tả'}

        PROFILE CONTEXT:
        - Agent profile: {profile.name if profile else 'general_analyst'}
        - Capabilities: {', '.join(profile.capabilities) if profile and hasattr(profile, 'capabilities') else 'General analysis'}

        INSTRUCTION:
        Hãy phân tích câu hỏi và cung cấp câu trả lời chính xác, chi tiết. 

        Nếu câu hỏi yêu cầu:
        1. ĐẾM/TỔNG SỐ (count, total, tổng cộng, có bao nhiêu): Sử dụng pandas count(), nunique(), len()
        2. THỐNG KÊ MÔ TẢ (average, mean, trung bình, max, min, mức cao nhất, thấp nhất): Sử dụng mean(), max(), min(), describe()
        3. TOP/RANK (top, cao nhất, thấp nhất, xếp hạng): Sử dụng nlargest(), nsmallest(), sort_values()
        4. NHÓM/PHÂN LOẠI (theo nhóm, by category, group by): Sử dụng groupby()
        5. LỌC DỮ LIỆU (filter, where, điều kiện): Sử dụng boolean indexing
        6. TÍNH TOÁN (tính, calculate, computation): Thực hiện phép tính phù hợp

        EXAMPLES của câu hỏi và cách xử lý:
        - "Tổng cộng có bao nhiêu sản phẩm?" → df.shape[0] hoặc len(df)
        - "Sản phẩm nào có giá mắc nhất?" → df.loc[df['gia'].idxmax(), 'ten_san_pham']
        - "Trung bình doanh thu theo tháng?" → df.groupby('thang')['doanh_thu'].mean()
        - "Top 5 khách hàng mua nhiều nhất?" → df.groupby('khach_hang')['so_luong'].sum().nlargest(5)

        QUESTION: {question}

        Hãy trả lời chính xác, cung cấp số liệu cụ thể và giải thích kết quả."""

        # Add profile-specific enhancements
        if profile and hasattr(profile, 'domain_knowledge') and profile.domain_knowledge:
            if 'metrics' in profile.domain_knowledge:
                base_prompt += f"\n\nKHI TÍNH TOÁN METRICS, ưu tiên: {', '.join(profile.domain_knowledge['metrics'])}"
            
            if 'business_terms' in profile.domain_knowledge:
                base_prompt += f"\n\nTHUẬT NGỮ BUSINESS: {', '.join(profile.domain_knowledge['business_terms'])}"
        
        return base_prompt
    
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
            # Clear all profiles for this dataset
            keys_to_remove = [key for key in self.agents.keys() if key.startswith(f"{dataset_id}_")]
            for key in keys_to_remove:
                self.agents.pop(key, None)
        else:
            self.agents.clear()
    
    async def get_dataset_insights(self, dataset_id: int, profile_name: str = "general_analyst") -> Dict[str, Any]:
        """Generate insights for a dataset using AI analysis"""
        logger.info(f"Generating dataset insights for dataset {dataset_id} with profile {profile_name}")
        
        try:
            # Get dataset information
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                logger.error(f"Dataset with id {dataset_id} not found")
                raise ValueError(f"Dataset with id {dataset_id} not found")
            
            # Get the agent for this dataset
            agent = self.get_or_create_agent(dataset_id, profile_name)
            
            # Generate basic insights using the agent
            insight_questions = [
                "What is the structure and overview of this dataset?",
                "What are the key statistics and patterns in the data?",
                "Are there any data quality issues or missing values?",
                "What are the most interesting findings in this data?"
            ]
            
            insights = {
                "dataset_info": {
                    "id": dataset.id,
                    "name": dataset.name,
                    "description": dataset.description,
                    "table_name": dataset.table_name
                },
                "ai_insights": [],
                "profile_used": profile_name,
                "generated_at": time.time()
            }
            
            # Generate AI insights for each question
            for question in insight_questions:
                try:
                    result = agent.chat(f"For dataset analysis: {question}")
                    insights["ai_insights"].append({
                        "question": question,
                        "insight": str(result),
                        "generated_successfully": True
                    })
                except Exception as e:
                    logger.warning(f"Failed to generate insight for question '{question}': {e}")
                    insights["ai_insights"].append({
                        "question": question,"insight": f"Unable to generate insight: {str(e)}",
                        "generated_successfully": False
                    })
            
            logger.info(f"Generated {len(insights['ai_insights'])} insights for dataset {dataset_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate dataset insights: {e}")
            logger.error(traceback.format_exc())
            raise Exception(f"Failed to generate dataset insights: {str(e)}")
    
    async def _try_smart_fallback(self, question: str, dataset_id: int) -> Optional[str]:
        """Try smart fallback agent for common queries"""
        try:
            logger.info("Trying smart fallback agent...")
            
            # Get dataset and load data for fallback agent
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return None
            
            # Load data using SQLAlchemy
            from sqlalchemy import create_engine
            engine = create_engine(settings.DATABASE_URL)
            df = pd.read_sql_table(dataset.table_name, engine)
            
            # Create smart fallback agent
            fallback_agent = SmartFallbackAgent(df)
            
            # Try to process with fallback
            result = fallback_agent.process_question(question)
            
            if result:
                logger.info("Smart fallback agent succeeded")
                return result
            
            return None
            
        except Exception as e:
            logger.warning(f"Smart fallback agent failed: {e}")
            return None
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available tools with their descriptions"""
        tools_info = []
        
        for tool_name, tool_instance in self.tools.items():
            tool_info = {
                "name": tool_name,
                "description": getattr(tool_instance, 'description', 'No description available'),
                "class_name": tool_instance.__class__.__name__
            }
            tools_info.append(tool_info)
        
        logger.debug(f"Listed {len(tools_info)} available tools")
        return tools_info
    
    def _convert_result_to_serializable(self, result: Any) -> str:
        """Convert PandasAI result to serializable format"""
        try:
            # If it's a pandas DataFrame, convert to string representation
            if hasattr(result, 'to_string'):
                logger.info("Converting DataFrame result to string")
                return result.to_string()
            
            # If it's a pandas Series, convert to string
            elif hasattr(result, 'to_list'):
                logger.info("Converting Series result to string")
                return str(result.to_list())
            
            # If it's already a string, return as-is
            elif isinstance(result, str):
                return result
            
            # If it's a number, convert to string
            elif isinstance(result, (int, float)):
                return str(result)
            
            # If it's a dict or list, convert to JSON string
            elif isinstance(result, (dict, list)):
                import json
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            # For anything else, convert to string
            else:
                logger.warning(f"Converting unknown type {type(result)} to string")
                return str(result)
                
        except Exception as e:
            logger.error(f"Error converting result to serializable format: {e}")
            return f"Result (type: {type(result).__name__}): {str(result)}"
