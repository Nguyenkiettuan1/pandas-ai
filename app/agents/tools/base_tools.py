from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class BaseTool(ABC):
    """Base class for all agent tools"""
    
    def __init__(self, name: str, description: str, enabled: bool = True):
        self.name = name
        self.description = description
        self.enabled = enabled
    
    @abstractmethod
    async def execute(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given data and parameters"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters"""
        return True
    
    def log_execution(self, parameters: Dict[str, Any], result: Dict[str, Any]):
        """Log tool execution"""
        logger.info(f"Tool {self.name} executed with params: {parameters}")

class DataDescriptionTool(BaseTool):
    """Tool for describing dataset characteristics"""
    
    def __init__(self):
        super().__init__(
            name="describe_data",
            description="Provide statistical description of dataset"
        )
    
    async def execute(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data description"""
        try:
            logger.debug(f"Describing dataset with shape: {data.shape}")
            
            description = {
                "shape": {
                    "rows": len(data),
                    "columns": len(data.columns)
                },
                "columns": list(data.columns),
                "data_types": data.dtypes.to_dict(),
                "missing_values": data.isnull().sum().to_dict(),
                "memory_usage": data.memory_usage(deep=True).sum(),
                "statistical_summary": {}
            }
            
            # Add statistical summary for numeric columns
            numeric_cols = data.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                description["statistical_summary"] = data[numeric_cols].describe().to_dict()
            
            # Add categorical summary
            categorical_cols = data.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                description["categorical_summary"] = {}
                for col in categorical_cols:
                    description["categorical_summary"][col] = {
                        "unique_values": data[col].nunique(),
                        "top_values": data[col].value_counts().head(5).to_dict()
                    }
            
            self.log_execution(parameters, description)
            return {"success": True, "data": description}
            
        except Exception as e:
            logger.error(f"Error in DataDescriptionTool: {e}")
            return {"success": False, "error": str(e)}

class DataFilterTool(BaseTool):
    """Tool for filtering data based on conditions"""
    
    def __init__(self):
        super().__init__(
            name="filter_data",
            description="Filter data based on conditions"
        )
    
    async def execute(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data based on conditions"""
        try:
            conditions = parameters.get("conditions", [])
            
            if not conditions:
                return {"success": False, "error": "No filter conditions provided"}
            
            filtered_data = data.copy()
            
            for condition in conditions:
                column = condition.get("column")
                operator = condition.get("operator")
                value = condition.get("value")
                
                if not all([column, operator, value is not None]):
                    continue
                
                if column not in data.columns:
                    logger.warning(f"Column {column} not found in dataset")
                    continue
                
                # Apply filter based on operator
                if operator == "==":
                    filtered_data = filtered_data[filtered_data[column] == value]
                elif operator == "!=":
                    filtered_data = filtered_data[filtered_data[column] != value]
                elif operator == ">":
                    filtered_data = filtered_data[filtered_data[column] > value]
                elif operator == ">=":
                    filtered_data = filtered_data[filtered_data[column] >= value]
                elif operator == "<":
                    filtered_data = filtered_data[filtered_data[column] < value]
                elif operator == "<=":
                    filtered_data = filtered_data[filtered_data[column] <= value]
                elif operator == "contains":
                    filtered_data = filtered_data[filtered_data[column].str.contains(str(value), na=False)]
                elif operator == "in":
                    filtered_data = filtered_data[filtered_data[column].isin(value)]
            
            result = {
                "original_rows": len(data),
                "filtered_rows": len(filtered_data),
                "conditions_applied": len(conditions),
                "data_preview": filtered_data.head(10).to_dict('records') if len(filtered_data) > 0 else []
            }
            
            logger.info(f"Filtered data from {len(data)} to {len(filtered_data)} rows")
            self.log_execution(parameters, result)
            
            return {"success": True, "data": result, "filtered_dataframe": filtered_data}
            
        except Exception as e:
            logger.error(f"Error in DataFilterTool: {e}")
            return {"success": False, "error": str(e)}

class DataAggregationTool(BaseTool):
    """Tool for aggregating data"""
    
    def __init__(self):
        super().__init__(
            name="aggregate_data",
            description="Group and aggregate data"
        )
    
    async def execute(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate data based on parameters"""
        try:
            group_by = parameters.get("group_by", [])
            aggregations = parameters.get("aggregations", {})
            
            if not group_by:
                return {"success": False, "error": "No group_by columns specified"}
            
            if not aggregations:
                return {"success": False, "error": "No aggregation functions specified"}
            
            # Validate group_by columns
            missing_cols = [col for col in group_by if col not in data.columns]
            if missing_cols:
                return {"success": False, "error": f"Columns not found: {missing_cols}"}
            
            # Perform aggregation
            grouped_data = data.groupby(group_by)
            result_data = grouped_data.agg(aggregations).reset_index()
            
            # Flatten column names if multi-level
            if isinstance(result_data.columns, pd.MultiIndex):
                result_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in result_data.columns]
            
            result = {
                "group_by_columns": group_by,
                "aggregation_functions": aggregations,
                "result_rows": len(result_data),
                "result_columns": list(result_data.columns),
                "data_preview": result_data.head(10).to_dict('records')
            }
            
            logger.info(f"Aggregated data into {len(result_data)} groups")
            self.log_execution(parameters, result)
            
            return {"success": True, "data": result, "aggregated_dataframe": result_data}
            
        except Exception as e:
            logger.error(f"Error in DataAggregationTool: {e}")
            return {"success": False, "error": str(e)}
