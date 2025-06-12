# Query Intent Analysis Service
from typing import Dict, Any, List, Optional
import re
from enum import Enum
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class QueryScope(Enum):
    """Defines the scope of query processing needed"""
    SINGLE = "single"           # Single dataset query (current behavior)
    MULTI = "multi"             # Multiple datasets, same type of analysis
    CROSS_DATASET = "cross_dataset"  # Cross-dataset analysis/joins
    DISCOVERY = "discovery"     # Find relevant datasets first


class QueryIntent(Enum):
    """Types of query intents"""
    RETRIEVAL = "retrieval"         # Show, display, list, get data
    AGGREGATION = "aggregation"     # Sum, count, average, total
    COMPARISON = "comparison"       # Compare, vs, difference
    RANKING = "ranking"            # Top, bottom, best, worst
    TREND_ANALYSIS = "trend_analysis"  # Over time, trends, patterns
    PREDICTION = "prediction"       # Forecast, predict, estimate
    EXPLORATION = "exploration"     # General data exploration
    FILTERING = "filtering"         # Where, filter, conditions


class QueryIntentAnalyzer:
    """
    Analyzes natural language queries to determine:
    1. Query scope (single/multi/cross-dataset)
    2. Query intent (what user wants to achieve)
    3. Required data types and domains
    4. Complexity level
    """
    
    def __init__(self):
        self.scope_patterns = self._initialize_scope_patterns()
        self.intent_patterns = self._initialize_intent_patterns()
        self.complexity_indicators = self._initialize_complexity_indicators()
        
    def analyze_query_scope(self, question: str) -> Dict[str, Any]:
        """
        Determine if query needs:
        - Single dataset (current behavior)  
        - Multiple datasets (cross-analysis)
        - Dataset discovery (find relevant data)
        
        Args:
            question: Natural language question
            
        Returns:
            Dict containing scope analysis results
        """
        question_lower = question.lower()
        
        scope_analysis = {
            "recommended_scope": QueryScope.SINGLE,
            "scope_confidence": 0.0,
            "scope_reasons": [],
            "multi_dataset_indicators": [],
            "cross_dataset_indicators": [],
            "discovery_indicators": []
        }
        
        # Check for multi-dataset indicators
        multi_indicators = self._detect_multi_dataset_patterns(question_lower)
        if multi_indicators:
            scope_analysis["multi_dataset_indicators"] = multi_indicators
            scope_analysis["recommended_scope"] = QueryScope.MULTI
            scope_analysis["scope_confidence"] = 0.7
            scope_analysis["scope_reasons"].append("Multiple dataset references detected")
            
        # Check for cross-dataset indicators  
        cross_indicators = self._detect_cross_dataset_patterns(question_lower)
        if cross_indicators:
            scope_analysis["cross_dataset_indicators"] = cross_indicators
            scope_analysis["recommended_scope"] = QueryScope.CROSS_DATASET
            scope_analysis["scope_confidence"] = 0.8
            scope_analysis["scope_reasons"].append("Cross-dataset analysis required")
            
        # Check for discovery indicators
        discovery_indicators = self._detect_discovery_patterns(question_lower)
        if discovery_indicators:
            scope_analysis["discovery_indicators"] = discovery_indicators
            if scope_analysis["recommended_scope"] == QueryScope.SINGLE:
                scope_analysis["recommended_scope"] = QueryScope.DISCOVERY
                scope_analysis["scope_confidence"] = 0.6
                scope_analysis["scope_reasons"].append("Dataset discovery needed")
        
        # Default to single dataset with lower confidence
        if scope_analysis["scope_confidence"] == 0.0:
            scope_analysis["scope_confidence"] = 0.5
            scope_analysis["scope_reasons"].append("No multi-dataset indicators found")
            
        logger.info(f"Query scope analysis: {scope_analysis['recommended_scope']} (confidence: {scope_analysis['scope_confidence']})")
        
        return scope_analysis
    
    def analyze_query_intent(self, question: str) -> Dict[str, Any]:
        """
        Analyze the intent of the query to understand what user wants to achieve
        
        Args:
            question: Natural language question
            
        Returns:
            Dict containing intent analysis results
        """
        question_lower = question.lower()
        
        intent_scores = {}
        intent_reasons = {}
        
        # Score each intent type
        for intent in QueryIntent:
            score, reasons = self._score_intent(question_lower, intent)
            intent_scores[intent] = score
            if reasons:
                intent_reasons[intent] = reasons
        
        # Find highest scoring intent
        primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
        primary_confidence = intent_scores[primary_intent]
        
        # Find secondary intents (above threshold)
        secondary_intents = [
            intent for intent, score in intent_scores.items() 
            if intent != primary_intent and score > 0.3
        ]
        
        intent_analysis = {
            "primary_intent": primary_intent,
            "primary_confidence": primary_confidence,
            "secondary_intents": secondary_intents,
            "intent_scores": {intent.value: score for intent, score in intent_scores.items()},
            "intent_reasons": {intent.value: reasons for intent, reasons in intent_reasons.items()},
            "complexity_level": self._assess_complexity(question_lower)
        }
        
        logger.info(f"Query intent analysis: {primary_intent.value} (confidence: {primary_confidence:.2f})")
        
        return intent_analysis
    
    def _initialize_scope_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for detecting query scope"""
        return {
            "multi_dataset": [
                r"compare.*across.*datasets?",
                r"all.*datasets?",
                r"multiple.*sources?",
                r"different.*tables?",
                r"various.*data.*sources?",
                r"from.*all.*data",
                r"tất cả.*dataset",
                r"nhiều.*nguồn.*dữ liệu"
            ],
            "cross_dataset": [
                r"join.*with",
                r"merge.*data",
                r"combine.*datasets?", 
                r"correlate.*between",
                r"relationship.*between.*datasets?",
                r"cross.*reference",
                r"kết hợp.*dữ liệu",
                r"liên kết.*với",
                r"so sánh.*giữa.*dataset"
            ],
            "discovery": [
                r"find.*data.*about",
                r"what.*data.*do.*we.*have",
                r"available.*datasets?",
                r"search.*for.*data",
                r"discover.*information",
                r"tìm.*dữ liệu.*về",
                r"có.*dữ liệu.*gì.*về",
                r"tìm.*kiếm.*thông tin"
            ]
        }
        
    def _initialize_intent_patterns(self) -> Dict[QueryIntent, List[str]]:
        """Initialize patterns for detecting query intent"""
        return {
            QueryIntent.RETRIEVAL: [
                r"show.*me", r"display", r"list", r"get.*data",
                r"what.*is", r"what.*are", r"hiển thị", r"cho.*tôi.*xem"
            ],
            QueryIntent.AGGREGATION: [
                r"total", r"sum", r"average", r"count", r"how.*many",
                r"tổng", r"trung bình", r"có.*bao.*nhiêu"
            ],
            QueryIntent.COMPARISON: [
                r"compare", r"vs", r"versus", r"difference.*between",
                r"so.*sánh", r"khác.*biệt.*giữa"
            ],
            QueryIntent.RANKING: [
                r"top.*\d+", r"bottom.*\d+", r"best", r"worst", r"highest", r"lowest",
                r"cao.*nhất", r"thấp.*nhất", r"tốt.*nhất", r"xấu.*nhất"
            ],
            QueryIntent.TREND_ANALYSIS: [
                r"trend", r"over.*time", r"monthly", r"daily", r"yearly",
                r"xu.*hướng", r"theo.*thời.*gian", r"hàng.*tháng"
            ],
            QueryIntent.PREDICTION: [
                r"predict", r"forecast", r"future", r"estimate", r"project",
                r"dự.*đoán", r"dự.*báo", r"tương.*lai"
            ],
            QueryIntent.FILTERING: [
                r"where", r"filter.*by", r"only.*show", r"with.*condition",
                r"lọc", r"điều.*kiện", r"chỉ.*hiển.*thị"
            ]
        }
        
    def _initialize_complexity_indicators(self) -> Dict[str, List[str]]:
        """Initialize patterns for assessing query complexity"""
        return {
            "high_complexity": [
                r"analyze.*correlation",
                r"statistical.*analysis", 
                r"machine.*learning",
                r"predict.*using",
                r"complex.*calculation",
                r"phân.*tích.*thống.*kê"
            ],
            "medium_complexity": [
                r"group.*by.*and",
                r"join.*multiple",
                r"aggregate.*with",
                r"compare.*across",
                r"nhóm.*theo.*và"
            ],
            "low_complexity": [
                r"show.*me",
                r"count.*rows?",
                r"simple.*list",
                r"basic.*info",
                r"hiển.*thị.*đơn.*giản"
            ]
        }
        
    def _detect_multi_dataset_patterns(self, question: str) -> List[str]:
        """Detect patterns indicating multi-dataset queries"""
        indicators = []
        for pattern in self.scope_patterns["multi_dataset"]:
            if re.search(pattern, question):
                indicators.append(pattern)
        return indicators
        
    def _detect_cross_dataset_patterns(self, question: str) -> List[str]:
        """Detect patterns indicating cross-dataset analysis"""
        indicators = []
        for pattern in self.scope_patterns["cross_dataset"]:
            if re.search(pattern, question):
                indicators.append(pattern)
        return indicators
        
    def _detect_discovery_patterns(self, question: str) -> List[str]:
        """Detect patterns indicating dataset discovery needed"""
        indicators = []
        for pattern in self.scope_patterns["discovery"]:
            if re.search(pattern, question):
                indicators.append(pattern)
        return indicators
        
    def _score_intent(self, question: str, intent: QueryIntent) -> tuple[float, List[str]]:
        """Score how well a question matches a specific intent"""
        patterns = self.intent_patterns.get(intent, [])
        matches = []
        score = 0.0
        
        for pattern in patterns:
            if re.search(pattern, question):
                matches.append(pattern)
                score += 1.0
                
        # Normalize score
        if patterns:
            score = min(score / len(patterns), 1.0)
            
        return score, matches
        
    def _assess_complexity(self, question: str) -> str:
        """Assess the complexity level of the query"""
        high_matches = sum(1 for pattern in self.complexity_indicators["high_complexity"] 
                          if re.search(pattern, question))
        medium_matches = sum(1 for pattern in self.complexity_indicators["medium_complexity"] 
                            if re.search(pattern, question))
        low_matches = sum(1 for pattern in self.complexity_indicators["low_complexity"] 
                         if re.search(pattern, question))
        
        if high_matches > 0:
            return "high"
        elif medium_matches > 0:
            return "medium"
        elif low_matches > 0:
            return "low"
        else:
            return "medium"  # default
            
    def analyze_complete_query(self, question: str) -> Dict[str, Any]:
        """
        Complete analysis combining scope and intent analysis
        
        Args:
            question: Natural language question
            
        Returns:
            Complete analysis results
        """
        scope_analysis = self.analyze_query_scope(question)
        intent_analysis = self.analyze_query_intent(question)
        
        complete_analysis = {
            "question": question,
            "scope_analysis": scope_analysis,
            "intent_analysis": intent_analysis,
            "processing_recommendations": self._generate_processing_recommendations(
                scope_analysis, intent_analysis
            )
        }
        
        return complete_analysis
        
    def _generate_processing_recommendations(
        self, 
        scope_analysis: Dict[str, Any], 
        intent_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate recommendations for how to process the query"""
        recommendations = {
            "agent_profile": "general_analyst",
            "dataset_selection_strategy": "single",
            "processing_approach": "standard",
            "additional_tools": []
        }
        
        # Recommend agent profile based on intent
        primary_intent = intent_analysis["primary_intent"]
        if primary_intent == QueryIntent.AGGREGATION:
            recommendations["agent_profile"] = "data_analyst"
        elif primary_intent == QueryIntent.COMPARISON:
            recommendations["agent_profile"] = "business_analyst"
        elif primary_intent == QueryIntent.PREDICTION:
            recommendations["agent_profile"] = "data_scientist"
        elif primary_intent == QueryIntent.TREND_ANALYSIS:
            recommendations["agent_profile"] = "time_series_analyst"
            
        # Recommend dataset selection strategy based on scope
        scope = scope_analysis["recommended_scope"]
        if scope == QueryScope.MULTI:
            recommendations["dataset_selection_strategy"] = "multi_select"
        elif scope == QueryScope.CROSS_DATASET:
            recommendations["dataset_selection_strategy"] = "cross_analysis"
        elif scope == QueryScope.DISCOVERY:
            recommendations["dataset_selection_strategy"] = "discovery_first"
            
        # Recommend processing approach based on complexity
        complexity = intent_analysis["complexity_level"]
        if complexity == "high":
            recommendations["processing_approach"] = "advanced_analytics"
            recommendations["additional_tools"] = ["statistical_analysis", "ml_models"]
        elif complexity == "medium":
            recommendations["processing_approach"] = "enhanced_processing"
            recommendations["additional_tools"] = ["data_visualization"]
            
        return recommendations
