from typing import Dict, Any, List
import pandas as pd
import logging
from .base_tools import BaseTool

logger = logging.getLogger(__name__)

class SalesSummaryTool(BaseTool):
    """Tool for generating comprehensive sales summaries"""
    
    def __init__(self):
        super().__init__(
            name="sales_summary",
            description="Generate comprehensive sales summaries"
        )
    
    async def execute(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sales summary"""
        try:
            # Expected columns for sales data
            amount_col = parameters.get("amount_column", "amount")
            date_col = parameters.get("date_column", "date")
            customer_col = parameters.get("customer_column", "customer_id")
            product_col = parameters.get("product_column", "product_id")
            
            # Validate required columns
            required_cols = [amount_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                return {"success": False, "error": f"Required columns missing: {missing_cols}"}
            
            summary = {
                "total_sales": float(data[amount_col].sum()),
                "average_sale": float(data[amount_col].mean()),
                "median_sale": float(data[amount_col].median()),
                "max_sale": float(data[amount_col].max()),
                "min_sale": float(data[amount_col].min()),
                "total_transactions": len(data)
            }
            
            # Add time-based analysis if date column exists
            if date_col in data.columns:
                data[date_col] = pd.to_datetime(data[date_col])
                summary["date_range"] = {
                    "start": data[date_col].min().isoformat(),
                    "end": data[date_col].max().isoformat()
                }
                
                # Monthly sales trend
                monthly_sales = data.groupby(data[date_col].dt.to_period('M'))[amount_col].sum()
                summary["monthly_trend"] = monthly_sales.to_dict()
            
            # Customer analysis if customer column exists
            if customer_col in data.columns:
                customer_stats = data.groupby(customer_col)[amount_col].agg(['sum', 'count', 'mean'])
                summary["customer_analysis"] = {
                    "unique_customers": data[customer_col].nunique(),
                    "avg_customer_value": float(customer_stats['sum'].mean()),
                    "top_customers": customer_stats.nlargest(5, 'sum')['sum'].to_dict()
                }
            
            # Product analysis if product column exists
            if product_col in data.columns:
                product_stats = data.groupby(product_col)[amount_col].agg(['sum', 'count'])
                summary["product_analysis"] = {
                    "unique_products": data[product_col].nunique(),
                    "top_products": product_stats.nlargest(5, 'sum')['sum'].to_dict()
                }
            
            logger.info(f"Generated sales summary for {len(data)} transactions")
            self.log_execution(parameters, summary)
            
            return {"success": True, "data": summary}
            
        except Exception as e:
            logger.error(f"Error in SalesSummaryTool: {e}")
            return {"success": False, "error": str(e)}

class CustomerAnalysisTool(BaseTool):
    """Tool for analyzing customer behavior and segments"""
    
    def __init__(self):
        super().__init__(
            name="customer_analysis",
            description="Analyze customer behavior and segments"
        )
    
    async def execute(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer behavior"""
        try:
            customer_col = parameters.get("customer_column", "customer_id")
            amount_col = parameters.get("amount_column", "amount")
            date_col = parameters.get("date_column", "date")
            
            if customer_col not in data.columns or amount_col not in data.columns:
                return {"success": False, "error": "Required customer or amount columns missing"}
            
            # Customer metrics
            customer_metrics = data.groupby(customer_col).agg({
                amount_col: ['sum', 'count', 'mean'],
                date_col: ['min', 'max'] if date_col in data.columns else []
            }).round(2)
            
            # Flatten column names
            customer_metrics.columns = ['_'.join(col).strip() for col in customer_metrics.columns]
            
            # Calculate customer lifetime value
            customer_metrics['customer_lifetime_value'] = customer_metrics[f'{amount_col}_sum']
            customer_metrics['avg_order_value'] = customer_metrics[f'{amount_col}_mean']
            customer_metrics['transaction_count'] = customer_metrics[f'{amount_col}_count']
            
            # Customer segmentation (simple RFM-like)
            customer_metrics['value_segment'] = pd.qcut(
                customer_metrics['customer_lifetime_value'], 
                q=3, 
                labels=['Low', 'Medium', 'High']
            )
            
            customer_metrics['frequency_segment'] = pd.qcut(
                customer_metrics['transaction_count'], 
                q=3, 
                labels=['Low', 'Medium', 'High']
            )
            
            analysis_result = {
                "total_customers": len(customer_metrics),
                "avg_customer_value": float(customer_metrics['customer_lifetime_value'].mean()),
                "top_10_customers": customer_metrics.nlargest(10, 'customer_lifetime_value')[
                    ['customer_lifetime_value', 'transaction_count', 'avg_order_value']
                ].to_dict('index'),
                "customer_segments": customer_metrics['value_segment'].value_counts().to_dict(),
                "frequency_segments": customer_metrics['frequency_segment'].value_counts().to_dict()
            }
            
            logger.info(f"Analyzed {len(customer_metrics)} customers")
            self.log_execution(parameters, analysis_result)
            
            return {"success": True, "data": analysis_result}
            
        except Exception as e:
            logger.error(f"Error in CustomerAnalysisTool: {e}")
            return {"success": False, "error": str(e)}

class PerformanceMetricsTool(BaseTool):
    """Tool for calculating business performance metrics"""
    
    def __init__(self):
        super().__init__(
            name="performance_metrics",
            description="Calculate KPIs and performance metrics"
        )
    
    async def execute(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        try:
            metrics_type = parameters.get("metrics_type", "sales")
            amount_col = parameters.get("amount_column", "amount")
            date_col = parameters.get("date_column", "date")
            
            metrics = {}
            
            if metrics_type == "sales":
                # Sales KPIs
                if amount_col in data.columns:
                    metrics["total_revenue"] = float(data[amount_col].sum())
                    metrics["average_deal_size"] = float(data[amount_col].mean())
                    metrics["total_deals"] = len(data)
                
                if date_col in data.columns:
                    data[date_col] = pd.to_datetime(data[date_col])
                    
                    # Growth rate calculation
                    monthly_revenue = data.groupby(data[date_col].dt.to_period('M'))[amount_col].sum()
                    if len(monthly_revenue) > 1:
                        latest_month = monthly_revenue.iloc[-1]
                        previous_month = monthly_revenue.iloc[-2]
                        growth_rate = ((latest_month - previous_month) / previous_month) * 100
                        metrics["month_over_month_growth"] = float(growth_rate)
            
            elif metrics_type == "customer":
                # Customer KPIs
                customer_col = parameters.get("customer_column", "customer_id")
                if customer_col in data.columns:
                    unique_customers = data[customer_col].nunique()
                    total_transactions = len(data)
                    
                    metrics["unique_customers"] = unique_customers
                    metrics["transactions_per_customer"] = total_transactions / unique_customers
                    
                    if amount_col in data.columns:
                        metrics["revenue_per_customer"] = float(data[amount_col].sum() / unique_customers)
            
            logger.info(f"Calculated {len(metrics)} performance metrics")
            self.log_execution(parameters, metrics)
            
            return {"success": True, "data": metrics}
            
        except Exception as e:
            logger.error(f"Error in PerformanceMetricsTool: {e}")
            return {"success": False, "error": str(e)}
