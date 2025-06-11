# Dataset Selection Service
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Tuple
import logging
from collections import defaultdict
import re

from app.core.response_handler import ResponseHandler, ResponseType
from app.models.dataset import Dataset
from app.schemas.context_schemas import DatasetSelectionMetadata

logger = logging.getLogger(__name__)


class DatasetSelectionService:
    """
    Service for intelligent dataset selection based on query content
    Uses NLP analysis to match queries with relevant datasets
    """

    def __init__(self, db: Session):
        self.db = db

    async def auto_select_datasets(
        self,
        question: str,
        available_datasets: List[int],
        max_datasets: int = 3,
        context_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Automatically select the most relevant datasets for a query
        
        Args:
            question: Natural language question
            available_datasets: List of dataset IDs to choose from
            max_datasets: Maximum number of datasets to select
            context_hint: Optional hint to guide selection
            
        Returns:
            Dict with selected datasets and selection metadata
        """
        try:
            if not available_datasets:
                return ResponseHandler.create_error_response(
                    error="No datasets available",
                    message="No datasets available for selection",
                    response_type=ResponseType.VALIDATION_ERROR
                )

            # Get dataset information
            datasets = self.db.query(Dataset).filter(Dataset.id.in_(available_datasets)).all()
            if not datasets:
                return ResponseHandler.create_error_response(
                    error="Datasets not found",
                    message="Available datasets not found in database",
                    response_type=ResponseType.VALIDATION_ERROR
                )

            # Analyze query for keywords and intent
            query_analysis = self._analyze_query(question, context_hint)
            
            # Score each dataset
            dataset_scores = {}
            for dataset in datasets:
                score = self._score_dataset_relevance(dataset, query_analysis)
                dataset_scores[dataset.id] = {
                    "score": score,
                    "dataset": dataset,
                    "reasoning": self._generate_selection_reasoning(dataset, query_analysis, score)
                }

            # Select top datasets
            sorted_datasets = sorted(
                dataset_scores.items(),
                key=lambda x: x[1]["score"],
                reverse=True
            )

            selected_count = min(max_datasets, len(sorted_datasets))
            selected_datasets = []
            selection_scores = {}
            reasoning_parts = []

            for i in range(selected_count):
                dataset_id, info = sorted_datasets[i]
                selected_datasets.append(dataset_id)
                selection_scores[dataset_id] = info["score"]
                reasoning_parts.append(f"Dataset {dataset_id} ({info['dataset'].name}): {info['reasoning']}")

            # Generate selection metadata
            selection_metadata = DatasetSelectionMetadata(
                strategy="auto_nlp",
                selected_datasets=selected_datasets,
                selection_scores=selection_scores,
                reasoning="; ".join(reasoning_parts),
                alternatives=[item[0] for item in sorted_datasets[selected_count:]]
            )

            result_data = {
                "selected_datasets": selected_datasets,
                "selection_metadata": selection_metadata.dict(),
                "query_analysis": query_analysis,
                "all_scores": {k: v["score"] for k, v in dataset_scores.items()}
            }

            logger.info(f"Auto-selected {len(selected_datasets)} datasets for query: '{question[:50]}...'")

            return ResponseHandler.create_success_response(
                data=result_data,
                message=f"Successfully selected {len(selected_datasets)} relevant datasets",
                response_type=ResponseType.GENERAL
            )

        except Exception as e:
            logger.error(f"Error in auto dataset selection: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to auto-select datasets",
                response_type=ResponseType.GENERAL
            )

    def _analyze_query(self, question: str, context_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze query to extract keywords and intent
        This is a simplified NLP analysis - can be enhanced with more sophisticated NLP libraries
        """
        question_lower = question.lower()
        context_lower = (context_hint or "").lower()
        combined_text = f"{question_lower} {context_lower}".strip()

        analysis = {
            "keywords": self._extract_keywords(combined_text),
            "intent": self._determine_intent(question_lower),
            "data_types": self._identify_data_types(combined_text),
            "time_scope": self._identify_time_scope(combined_text),
            "aggregation_type": self._identify_aggregation_type(question_lower)
        }

        return analysis

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from query text"""
        # Common business/data keywords
        business_keywords = [
            "sales", "revenue", "profit", "customer", "product", "order", "transaction",
            "marketing", "campaign", "conversion", "lead", "opportunity",
            "inventory", "stock", "supply", "demand", "logistics",
            "financial", "budget", "cost", "expense", "income",
            "performance", "metric", "kpi", "analytics", "report"
        ]

        # Technical keywords
        technical_keywords = [
            "data", "database", "table", "record", "field", "column",
            "analysis", "statistics", "trend", "pattern", "correlation"
        ]

        all_keywords = business_keywords + technical_keywords
        found_keywords = [kw for kw in all_keywords if kw in text]
        
        # Also extract potential custom keywords (2-3 character words)
        words = re.findall(r'\b[a-z]{3,}\b', text)
        custom_keywords = [w for w in words if w not in found_keywords][:5]  # Limit to 5
        
        return found_keywords + custom_keywords

    def _determine_intent(self, question: str) -> str:
        """Determine the intent of the query"""
        if any(word in question for word in ["show", "display", "list", "get"]):
            return "retrieval"
        elif any(word in question for word in ["compare", "vs", "versus", "difference"]):
            return "comparison"
        elif any(word in question for word in ["trend", "over time", "monthly", "daily", "yearly"]):
            return "trend_analysis"
        elif any(word in question for word in ["top", "bottom", "best", "worst", "highest", "lowest"]):
            return "ranking"
        elif any(word in question for word in ["total", "sum", "average", "count", "aggregate"]):
            return "aggregation"
        elif any(word in question for word in ["predict", "forecast", "future", "estimate"]):
            return "prediction"
        else:
            return "exploration"

    def _identify_data_types(self, text: str) -> List[str]:
        """Identify what types of data the query is asking about"""
        data_types = []
        
        if any(word in text for word in ["sales", "revenue", "income", "profit"]):
            data_types.append("financial")
        if any(word in text for word in ["customer", "client", "user", "buyer"]):
            data_types.append("customer")
        if any(word in text for word in ["product", "item", "goods", "service"]):
            data_types.append("product")
        if any(word in text for word in ["order", "transaction", "purchase", "sale"]):
            data_types.append("transactional")
        if any(word in text for word in ["marketing", "campaign", "advertisement", "promotion"]):
            data_types.append("marketing")
        if any(word in text for word in ["inventory", "stock", "warehouse", "supply"]):
            data_types.append("inventory")
            
        return data_types if data_types else ["general"]

    def _identify_time_scope(self, text: str) -> Optional[str]:
        """Identify time scope mentioned in the query"""
        if any(word in text for word in ["today", "daily", "day"]):
            return "daily"
        elif any(word in text for word in ["week", "weekly"]):
            return "weekly"
        elif any(word in text for word in ["month", "monthly"]):
            return "monthly"
        elif any(word in text for word in ["quarter", "quarterly", "q1", "q2", "q3", "q4"]):
            return "quarterly"
        elif any(word in text for word in ["year", "yearly", "annual"]):
            return "yearly"
        elif any(word in text for word in ["real-time", "live", "current"]):
            return "real_time"
        else:
            return None

    def _identify_aggregation_type(self, question: str) -> Optional[str]:
        """Identify type of aggregation needed"""
        if any(word in question for word in ["sum", "total"]):
            return "sum"
        elif any(word in question for word in ["average", "avg", "mean"]):
            return "average"
        elif any(word in question for word in ["count", "number of", "how many"]):
            return "count"
        elif any(word in question for word in ["max", "maximum", "highest", "top"]):
            return "max"
        elif any(word in question for word in ["min", "minimum", "lowest", "bottom"]):
            return "min"
        else:
            return None

    def _score_dataset_relevance(self, dataset: Dataset, query_analysis: Dict[str, Any]) -> float:
        """
        Score how relevant a dataset is to the query
        Returns a score between 0 and 1
        """
        score = 0.0
        max_score = 0.0

        # Score based on dataset name matching keywords
        dataset_name_lower = dataset.name.lower()
        dataset_desc_lower = (dataset.description or "").lower()
        table_name_lower = (dataset.table_name or "").lower()

        # Keyword matching (40% of score)
        keyword_score = 0.0
        for keyword in query_analysis["keywords"]:
            if keyword in dataset_name_lower:
                keyword_score += 3.0  # Name match is most important
            elif keyword in table_name_lower:
                keyword_score += 2.0  # Table name match is second
            elif keyword in dataset_desc_lower:
                keyword_score += 1.0  # Description match is least important

        # Normalize keyword score
        if query_analysis["keywords"]:
            keyword_score = min(keyword_score / (len(query_analysis["keywords"]) * 3), 1.0)
        score += keyword_score * 0.4
        max_score += 0.4

        # Score based on data types (30% of score)
        data_type_score = 0.0
        for data_type in query_analysis["data_types"]:
            if data_type in dataset_name_lower or data_type in dataset_desc_lower:
                data_type_score += 1.0

        if query_analysis["data_types"]:
            data_type_score = min(data_type_score / len(query_analysis["data_types"]), 1.0)
        score += data_type_score * 0.3
        max_score += 0.3

        # Score based on dataset metadata (20% of score)
        # This is where we could add more sophisticated scoring based on:
        # - Dataset size
        # - Data freshness
        # - Query history
        # - User preferences
        metadata_score = 0.5  # Default moderate score
        score += metadata_score * 0.2
        max_score += 0.2

        # Intent-based scoring (10% of score)
        intent_score = 0.5  # Default moderate score
        # Could enhance this with dataset-specific intent scoring
        score += intent_score * 0.1
        max_score += 0.1

        # Normalize final score
        final_score = score / max_score if max_score > 0 else 0.0
        return round(final_score, 3)

    def _generate_selection_reasoning(self, dataset: Dataset, query_analysis: Dict[str, Any], score: float) -> str:
        """Generate human-readable reasoning for dataset selection"""
        reasons = []

        # Keyword matches
        dataset_text = f"{dataset.name} {dataset.description or ''} {dataset.table_name or ''}".lower()
        matching_keywords = [kw for kw in query_analysis["keywords"] if kw in dataset_text]
        if matching_keywords:
            reasons.append(f"matches keywords: {', '.join(matching_keywords[:3])}")

        # Data type matches
        matching_types = [dt for dt in query_analysis["data_types"] if dt in dataset_text]
        if matching_types:
            reasons.append(f"contains {', '.join(matching_types)} data")

        # Score interpretation
        if score >= 0.8:
            confidence = "high confidence"
        elif score >= 0.6:
            confidence = "good match"
        elif score >= 0.4:
            confidence = "moderate match"
        else:
            confidence = "low match"

        if reasons:
            return f"{confidence} - {'; '.join(reasons)}"
        else:
            return f"{confidence} - general relevance"
