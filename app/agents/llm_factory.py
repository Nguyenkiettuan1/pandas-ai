#!/usr/bin/env python3
"""
LLM Factory for creating and managing Language Model clients
"""
from typing import Dict, Any, Optional
from pandasai.llm import OpenAI, BambooLLM
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class LLMFactory:
    """Factory class for creating and managing LLM clients"""
    
    _instance = None
    _llm_cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMFactory, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            logger.info("LLM Factory initialized")
    
    def create_llm(self, config: Dict[str, Any] = None) -> Any:
        """Create LLM client based on configuration"""
        config = config or {}
        
        # Create cache key from config
        cache_key = self._create_cache_key(config)
        
        # Return cached LLM if exists
        if cache_key in self._llm_cache:
            logger.debug(f"Using cached LLM for config: {cache_key}")
            return self._llm_cache[cache_key]
        
        # Create new LLM
        llm = self._create_new_llm(config)
        
        # Cache the LLM
        self._llm_cache[cache_key] = llm
        logger.debug(f"Created and cached new LLM: {cache_key}")
        
        return llm
    
    def _create_new_llm(self, config: Dict[str, Any]) -> Any:
        """Create a new LLM instance"""
        
        # Check for PandasAI Cloud first
        if settings.USE_PANDASAI_CLOUD and settings.PANDASAI_API_KEY:
            logger.info("Creating PandasAI Cloud LLM")
            return BambooLLM(api_key=settings.PANDASAI_API_KEY)
        
        # Use OpenAI
        elif settings.OPENAI_API_KEY:
            logger.info("Creating OpenAI LLM")
            
            # Get model from config
            model = config.get("llm_model", "gpt-4")
            temperature = config.get("temperature", 0.1)
            max_tokens = config.get("max_tokens", 2000)
            
            logger.debug(f"OpenAI Config - Model: {model}, Temp: {temperature}, Max tokens: {max_tokens}")
            
            try:
                # Check if it's an OpenRouter key
                if settings.OPENAI_API_KEY.startswith("sk-or-"):
                    logger.info("Detected OpenRouter API key")
                    return OpenAI(
                        api_token=settings.OPENAI_API_KEY,
                        base_url="https://openrouter.ai/api/v1",
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                else:
                    logger.info("Using direct OpenAI API")
                    return OpenAI(
                        api_token=settings.OPENAI_API_KEY,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
            except Exception as e:
                logger.error(f"Failed to create OpenAI LLM: {e}")
                raise Exception(f"Failed to initialize OpenAI LLM: {e}")
        
        else:
            logger.warning("No valid LLM configuration found")
            return self._create_mock_llm()
    
    def _create_mock_llm(self):
        """Create a mock LLM for testing"""
        class MockLLM:
            def __init__(self):
                self.model = "mock-llm"
                logger.warning("Using Mock LLM - please configure a real LLM for production")
            
            def generate_response(self, prompt):
                return "This is a mock response. Please configure OPENAI_API_KEY or PANDASAI_API_KEY."
            
            def chat(self, prompt):
                return self.generate_response(prompt)
        
        return MockLLM()
    
    def _create_cache_key(self, config: Dict[str, Any]) -> str:
        """Create a cache key from config"""
        model = config.get("llm_model", "gpt-4o-mini")
        temperature = config.get("temperature", 0.1)
        max_tokens = config.get("max_tokens", 2000)
        
        return f"{model}_{temperature}_{max_tokens}"
    
    def clear_cache(self):
        """Clear the LLM cache"""
        self._llm_cache.clear()
        logger.info("LLM cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        return {
            "cached_llms": len(self._llm_cache),
            "cache_keys": list(self._llm_cache.keys())
        }

# Global instance
llm_factory = LLMFactory()
