# filepath: d:\PandasAI\app\routes\dataset_routes.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
from app.core.database import get_db
from app.core.response_handler import ResponseHandler, ResponseType, HTTPStatusCode
from app.services.dataset_service import DatasetService
from app.schemas.dataset_schemas import DatasetCreate, DatasetUpdate, DatasetResponse

# Create router for dataset endpoints
dataset_router = APIRouter(prefix="/datasets", tags=["Datasets"])

@dataset_router.post("/create", response_model=Dict[str, Any])
async def create_dataset(
    dataset: DatasetCreate,
    db: Session = Depends(get_db)
):
    """Create a new dataset"""
    try:
        service = DatasetService(db)
        result = await service.create_dataset(
            name=dataset.name,
            description=dataset.description,
            file_path=dataset.file_path,
            table_name=dataset.table_name
        )
        return result
    except Exception as e:
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error creating dataset",
            response_type=ResponseType.GENERAL,
            status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@dataset_router.get("/", response_model=Dict[str, Any])
async def get_datasets(db: Session = Depends(get_db)):
    """Get all datasets"""
    try:
        service = DatasetService(db)
        return await service.get_datasets()
    except Exception as e:
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error retrieving datasets",
            response_type=ResponseType.GENERAL,
            status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@dataset_router.get("/{dataset_id}", response_model=Dict[str, Any])
async def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific dataset"""
    try:
        service = DatasetService(db)
        return await service.get_dataset(dataset_id)
    except Exception as e:
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error retrieving dataset",
            response_type=ResponseType.GENERAL,
            status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@dataset_router.get("/{dataset_id}/insights", response_model=Dict[str, Any])
async def get_dataset_insights(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """Get insights for a specific dataset"""
    try:
        service = DatasetService(db)
        return await service.get_dataset_insights(dataset_id)
    except Exception as e:
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error generating dataset insights",
            response_type=ResponseType.DATASET_INSIGHT,
            status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@dataset_router.put("/{dataset_id}", response_model=Dict[str, Any])
async def update_dataset(
    dataset_id: int,
    dataset_update: DatasetUpdate,
    db: Session = Depends(get_db)
):
    """Update a dataset"""
    try:
        service = DatasetService(db)
        result = await service.update_dataset(
            dataset_id=dataset_id,
            name=dataset_update.name,
            description=dataset_update.description
        )
        if not result:
            return ResponseHandler.create_not_found_response(
                resource="Dataset",
                resource_id=dataset_id
            )
        return result
    except Exception as e:
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error updating dataset",
            response_type=ResponseType.GENERAL,
            status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@dataset_router.delete("/{dataset_id}", response_model=Dict[str, Any])
async def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """Delete a dataset"""
    try:
        service = DatasetService(db)
        success = await service.delete_dataset(dataset_id)
        if not success:
            return ResponseHandler.create_not_found_response(
                resource="Dataset",
                resource_id=dataset_id
            )
        return ResponseHandler.create_success_response(
            data={"dataset_id": dataset_id},
            message="Dataset deleted successfully",
            response_type=ResponseType.GENERAL,
            status_code=HTTPStatusCode.OK
        )
    except Exception as e:
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error deleting dataset",
            response_type=ResponseType.GENERAL,
            status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@dataset_router.post("/upload-csv/", response_model=Dict[str, Any])
async def upload_csv_dataset(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    db: Session = Depends(get_db)
):
    """Upload CSV file to create a dataset"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            return ResponseHandler.create_validation_error_response(
                errors=["File must be a CSV format"],
                message="Invalid file type"
            )
        
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create dataset
        service = DatasetService(db)
        dataset_name = name or file.filename.replace('.csv', '')
        
        result = await service.load_csv_to_dataset(
            name=dataset_name,
            csv_file_path=file_path,
            description=description
        )
        
        return result
        
    except Exception as e:
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error uploading CSV",
            response_type=ResponseType.GENERAL,
            status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )
