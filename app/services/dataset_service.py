from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.core.response_handler import ResponseHandler, ResponseType
from app.core.logging_config import get_logger
import pandas as pd

logger = get_logger(__name__)

class DatasetService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_dataset(
        self, 
        name: str, 
        description: str = None, 
        file_path: str = None,
        table_name: str = None
    ) -> Dict[str, Any]:
        """Create a new dataset"""
        try:
            logger.info(f"Creating dataset: {name}")
            
            # Validate inputs
            if not name or not name.strip():
                return ResponseHandler.create_error_response(
                    error="Dataset name cannot be empty",
                    message="Dataset creation validation failed",
                    response_type=ResponseType.VALIDATION
                )
            
            dataset = Dataset(
                name=name.strip(),
                description=description,
                file_path=file_path,
                table_name=table_name or name.lower().replace(" ", "_")
            )
            
            self.db.add(dataset)
            self.db.commit()
            self.db.refresh(dataset)
            
            logger.info(f"Dataset created successfully with ID: {dataset.id}")
            
            return ResponseHandler.create_success_response(
                data={
                    "id": dataset.id,
                    "name": dataset.name,
                    "description": dataset.description,
                    "file_path": dataset.file_path,
                    "table_name": dataset.table_name,
                    "created_at": dataset.created_at
                },
                message="Dataset created successfully",
                response_type=ResponseType.GENERAL
            )
            
        except Exception as e:
            logger.error(f"Error creating dataset: {e}")
            self.db.rollback()
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to create dataset",
                response_type=ResponseType.GENERAL
            )
        
    async def get_dataset(self, dataset_id: int) -> Dict[str, Any]:
        """Get a dataset by ID"""
        try:
            logger.debug(f"Getting dataset with ID: {dataset_id}")
            
            if not isinstance(dataset_id, int) or dataset_id <= 0:
                return ResponseHandler.create_error_response(
                    error="Invalid dataset ID",
                    message="Dataset ID must be a positive integer",
                    response_type=ResponseType.VALIDATION
                )
            
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                return ResponseHandler.create_error_response(
                    error="Dataset not found",
                    message=f"No dataset found with ID: {dataset_id}",
                    response_type=ResponseType.GENERAL
                )
            
            dataset_data = {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "file_path": dataset.file_path,
                "table_name": dataset.table_name,
                "is_active": dataset.is_active,
                "created_at": dataset.created_at,
                "updated_at": dataset.updated_at
            }
            
            logger.debug(f"Successfully retrieved dataset: {dataset.name}")
            
            return ResponseHandler.create_success_response(
                data=dataset_data,
                message="Dataset retrieved successfully",
                response_type=ResponseType.GENERAL
            )
            
        except Exception as e:
            logger.error(f"Error getting dataset {dataset_id}: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to retrieve dataset",
                response_type=ResponseType.GENERAL
            )

    async def get_datasets(self) -> Dict[str, Any]:
        """Get all active datasets"""
        try:
            logger.debug("Getting all active datasets")
            
            datasets = self.db.query(Dataset).filter(Dataset.is_active == True).all()
            
            datasets_data = [
                {
                    "id": dataset.id,
                    "name": dataset.name,
                    "description": dataset.description,
                    "file_path": dataset.file_path,
                    "table_name": dataset.table_name,
                    "is_active": dataset.is_active,
                    "created_at": dataset.created_at,
                    "updated_at": dataset.updated_at
                }
                for dataset in datasets
            ]
            
            logger.info(f"Retrieved {len(datasets_data)} active datasets")
            
            return ResponseHandler.create_success_response(
                data=datasets_data,
                message=f"Retrieved {len(datasets_data)} datasets",
                response_type=ResponseType.GENERAL,
                metadata={"total_count": len(datasets_data)}
            )
            
        except Exception as e:
            logger.error(f"Error getting datasets: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to retrieve datasets",
                response_type=ResponseType.GENERAL
            )

    async def update_dataset(
        self, 
        dataset_id: int, 
        name: str = None, 
        description: str = None
    ) -> Dict[str, Any]:
        """Update a dataset"""
        try:
            logger.info(f"Updating dataset {dataset_id}")
            
            # Get existing dataset first
            dataset_response = await self.get_dataset(dataset_id)
            if not ResponseHandler.is_success(dataset_response):
                return dataset_response
            
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if name and name.strip():
                dataset.name = name.strip()
            if description is not None:
                dataset.description = description
            
            self.db.commit()
            self.db.refresh(dataset)
            
            logger.info(f"Dataset {dataset_id} updated successfully")
            
            return ResponseHandler.create_success_response(
                data={
                    "id": dataset.id,
                    "name": dataset.name,
                    "description": dataset.description,
                    "updated_at": dataset.updated_at
                },
                message="Dataset updated successfully",
                response_type=ResponseType.GENERAL
            )
            
        except Exception as e:
            logger.error(f"Error updating dataset {dataset_id}: {e}")
            self.db.rollback()
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to update dataset",
                response_type=ResponseType.GENERAL
            )

    async def delete_dataset(self, dataset_id: int) -> Dict[str, Any]:
        """Delete a dataset (soft delete)"""
        try:
            logger.info(f"Deleting dataset {dataset_id}")
            
            # Get existing dataset first
            dataset_response = await self.get_dataset(dataset_id)
            if not ResponseHandler.is_success(dataset_response):
                return dataset_response
            
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            dataset.is_active = False
            
            self.db.commit()
            
            logger.info(f"Dataset {dataset_id} deleted successfully")
            
            return ResponseHandler.create_success_response(
                data={"id": dataset_id, "deleted": True},
                message="Dataset deleted successfully",
                response_type=ResponseType.GENERAL
            )
            
        except Exception as e:
            logger.error(f"Error deleting dataset {dataset_id}: {e}")
            self.db.rollback()
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to delete dataset",
                response_type=ResponseType.GENERAL
            )
    
    async def load_csv_to_dataset(
        self, 
        name: str, 
        csv_file_path: str, 
        description: str = None
    ) -> Dict[str, Any]:
        """Load CSV file data to create a dataset"""
        try:
            logger.info(f"Loading CSV file to create dataset: {name}")
            
            # Read CSV file to validate it
            df = pd.read_csv(csv_file_path)
            logger.info(f"CSV file loaded successfully, shape: {df.shape}")
            
            # Create dataset record
            dataset_response = await self.create_dataset(
                name=name,
                description=description,
                file_path=csv_file_path,
                table_name=name.lower().replace(" ", "_").replace("-", "_")
            )
            
            if not ResponseHandler.is_success(dataset_response):
                return dataset_response
            
            # Here you would typically load the data into PostgreSQL
            # For now, we'll just return the dataset creation response
            # In production, you'd use pandas.to_sql() or similar
            
            logger.info(f"Dataset created successfully from CSV: {name}")
            return dataset_response
            
        except Exception as e:
            logger.error(f"Failed to load CSV to dataset: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message=f"Failed to load CSV file: {str(e)}",
                response_type=ResponseType.GENERAL
            )
    
    async def get_dataset_insights(self, dataset_id: int) -> Dict[str, Any]:
        """Get insights for a dataset"""
        try:
            logger.info(f"Getting insights for dataset {dataset_id}")
            
            # First, validate the dataset exists
            dataset_response = await self.get_dataset(dataset_id)
            if not ResponseHandler.is_success(dataset_response):
                return dataset_response
            
            dataset_data = dataset_response['data']
            
            # For now, provide basic dataset information as insights
            # In production, you would analyze the actual data
            insights = {
                "dataset_info": {
                    "id": dataset_data['id'],
                    "name": dataset_data['name'],
                    "description": dataset_data['description'],
                    "table_name": dataset_data['table_name'],
                    "created_at": dataset_data['created_at']
                },
                "basic_insights": {
                    "dataset_exists": True,
                    "table_configured": dataset_data['table_name'] is not None,
                    "has_description": dataset_data['description'] is not None,
                    "status": "active" if dataset_data['is_active'] else "inactive"
                },
                "recommendations": [
                    "Use natural language queries to explore this dataset",
                    "Consider using different agent profiles for specialized analysis",
                    "Check query history to see previous analysis patterns"                ]
            }
            
            # TODO: In production, add actual data analysis here:
            # - Row count, column count
            # - Data types analysis
            # - Missing values analysis
            # - Basic statistics
            # - Data quality metrics
            
            logger.info(f"Generated insights for dataset {dataset_id}")
            
            return ResponseHandler.create_dataset_insights_response(
                insights=insights,
                dataset_id=dataset_id,
                profile_name="general_analyst",  # Default profile for dataset insights
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error getting dataset insights for {dataset_id}: {e}")
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to generate dataset insights",
                response_type=ResponseType.DATASET_INSIGHT
            )
