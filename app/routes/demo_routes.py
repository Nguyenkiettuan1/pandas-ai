from fastapi import APIRouter, Depends, Query as FastAPIQuery
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from app.core.database import get_db
from app.core.response_handler import ResponseHandler, ResponseType
from app.core.response_utils import (
    handle_service_response, 
    validate_and_extract_data,
    merge_responses,
    create_paginated_response,
    execute_with_timeout,
    ResponseBuilder
)
from app.core.logging_config import get_logger
from app.services.query_service import QueryService
import asyncio
import random

logger = get_logger(__name__)

# Create router for demo endpoints
demo_router = APIRouter(prefix="/demo", tags=["Demo"])

@demo_router.get("/response-format/", response_model=Dict[str, Any])
async def demo_response_format():
    """Demonstrate different response formats"""
    
    # Success response
    success_response = ResponseHandler.create_success_response(
        data={"message": "This is a success response", "value": 42},
        message="Operation completed successfully",
        response_type=ResponseType.GENERAL,
        metadata={"demo": True, "timestamp": "2025-06-11"}
    )
    
    # Error response (for demonstration)
    error_response = ResponseHandler.create_error_response(
        error="This is a demo error",
        message="This demonstrates an error response",
        response_type=ResponseType.GENERAL
    )
    
    # Warning response
    warning_response = ResponseHandler.create_warning_response(
        data={"processed_items": 95, "total_items": 100},
        message="Processing completed with warnings",
        warnings=["5 items could not be processed", "Memory usage is high"],
        response_type=ResponseType.GENERAL
    )
    
    # Partial success response
    partial_response = ResponseHandler.create_partial_success_response(
        data={"completed_tasks": 7, "total_tasks": 10},
        message="Batch operation partially completed",
        warnings=["3 tasks failed due to timeout"],
        response_type=ResponseType.GENERAL
    )
    
    return ResponseHandler.create_success_response(
        data={
            "examples": {
                "success": success_response,
                "error": error_response,
                "warning": warning_response,
                "partial_success": partial_response
            }
        },
        message="Response format examples generated",
        response_type=ResponseType.GENERAL
    )

@demo_router.get("/response-builder/", response_model=Dict[str, Any])
async def demo_response_builder(
    include_warnings: bool = FastAPIQuery(default=False),
    include_errors: bool = FastAPIQuery(default=False)
):
    """Demonstrate ResponseBuilder pattern"""
    
    builder = ResponseBuilder(ResponseType.GENERAL)
    builder.with_data({"items_processed": 150, "total_time": "2.5s"})
    builder.with_message("Processing completed")
    builder.with_metadata("batch_id", "demo-batch-001")
    builder.with_metadata("processor_version", "1.0.0")
    
    if include_warnings:
        builder.with_warning("Some items were skipped due to invalid format")
        builder.with_warning("Memory usage exceeded 80%")
    
    if include_errors:
        builder.with_error("Database connection was briefly interrupted")
        builder.with_error("External API rate limit exceeded")
    
    return builder.build()

@demo_router.get("/batch-processing/", response_model=Dict[str, Any])
async def demo_batch_processing(
    items_count: int = FastAPIQuery(default=5, ge=1, le=20),
    failure_rate: float = FastAPIQuery(default=0.2, ge=0.0, le=1.0)
):
    """Demonstrate batch processing with response merging"""
    
    async def process_single_item(item_id: int) -> Dict[str, Any]:
        """Simulate processing a single item"""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Randomly fail some items based on failure_rate
        if random.random() < failure_rate:
            return ResponseHandler.create_error_response(
                error=f"Processing failed for item {item_id}",
                message="Item processing error",
                response_type=ResponseType.GENERAL
            )
        else:
            return ResponseHandler.create_success_response(
                data={"item_id": item_id, "processed_value": item_id * 2},
                message=f"Item {item_id} processed successfully",
                response_type=ResponseType.GENERAL
            )
    
    logger.info(f"Starting batch processing of {items_count} items")
    
    # Process all items
    responses = []
    for i in range(1, items_count + 1):
        response = await process_single_item(i)
        responses.append(response)
    
    # Merge all responses
    return merge_responses(responses, "demo_batch_processing")

@demo_router.get("/pagination/", response_model=Dict[str, Any])
async def demo_pagination(
    page: int = FastAPIQuery(default=1, ge=1),
    page_size: int = FastAPIQuery(default=5, ge=1, le=50)
):
    """Demonstrate paginated responses"""
    
    # Generate demo data
    total_items = 47  # Simulate having 47 total items
    demo_data = [
        {
            "id": i,
            "name": f"Item {i}",
            "value": i * 10,
            "category": f"Category {(i % 5) + 1}"
        }
        for i in range(1, total_items + 1)
    ]
    
    return create_paginated_response(
        data=demo_data,
        page=page,
        page_size=page_size,
        total_count=total_items
    )

@demo_router.get("/timeout-demo/", response_model=Dict[str, Any])
async def demo_timeout_handling(
    operation_duration: float = FastAPIQuery(default=1.0, ge=0.1, le=10.0),
    timeout_limit: float = FastAPIQuery(default=2.0, ge=0.5, le=5.0)
):
    """Demonstrate timeout handling"""
    
    async def long_running_operation():
        """Simulate a long-running operation"""
        logger.info(f"Starting operation that will take {operation_duration} seconds")
        await asyncio.sleep(operation_duration)
        return {"result": "Operation completed", "duration": operation_duration}
    
    return await execute_with_timeout(
        operation=long_running_operation,
        timeout_seconds=timeout_limit,
        operation_name="demo_long_operation"
    )

@demo_router.get("/service-integration/", response_model=Dict[str, Any])
async def demo_service_integration(
    dataset_id: int = FastAPIQuery(default=1),
    db: Session = Depends(get_db)
):
    """Demonstrate integration with actual service responses"""
    
    try:
        service = QueryService(db)
        
        # Get service health
        health_response = await service.get_service_health()
        health_success, health_data, health_error = validate_and_extract_data(health_response)
        
        # Get query statistics
        stats_response = await service.get_query_statistics(dataset_id)
        stats_success, stats_data, stats_error = validate_and_extract_data(stats_response)
        
        # Combine results
        builder = ResponseBuilder(ResponseType.GENERAL)
        builder.with_message("Service integration demo completed")
        builder.with_metadata("dataset_id", dataset_id)
        
        combined_data = {}
        
        if health_success:
            combined_data["health"] = health_data
        else:
            builder.with_warning(f"Health check failed: {health_error}")
            combined_data["health"] = None
        
        if stats_success:
            combined_data["statistics"] = stats_data
        else:
            builder.with_warning(f"Statistics retrieval failed: {stats_error}")
            combined_data["statistics"] = None
        
        return builder.with_data(combined_data).build()
        
    except Exception as e:
        logger.error(f"Error in service integration demo: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Service integration demo failed",
            response_type=ResponseType.GENERAL
        )

@demo_router.get("/validation-patterns/", response_model=Dict[str, Any])
async def demo_validation_patterns(
    name: Optional[str] = None,
    age: Optional[int] = None,
    email: Optional[str] = None
):
    """Demonstrate validation patterns"""
    
    builder = ResponseBuilder(ResponseType.VALIDATION)
    errors = []
    warnings = []
    validated_data = {}
    
    # Validate name
    if name is None:
        errors.append("Name is required")
    elif len(name.strip()) < 2:
        errors.append("Name must be at least 2 characters long")
    elif len(name) > 50:
        warnings.append("Name is quite long")
        validated_data["name"] = name[:50]
    else:
        validated_data["name"] = name.strip()
    
    # Validate age
    if age is None:
        warnings.append("Age not provided, defaulting to 0")
        validated_data["age"] = 0
    elif age < 0:
        errors.append("Age cannot be negative")
    elif age > 150:
        errors.append("Age seems unrealistic")
    else:
        validated_data["age"] = age
    
    # Validate email
    if email is None:
        warnings.append("Email not provided")
    elif "@" not in email:
        errors.append("Email must contain @ symbol")
    else:
        validated_data["email"] = email.lower()
    
    # Build response
    for error in errors:
        builder.with_error(error)
    
    for warning in warnings:
        builder.with_warning(warning)
    
    builder.with_data(validated_data)
    builder.with_metadata("validation_rules", {
        "name": "Required, 2-50 characters",
        "age": "Optional, 0-150",
        "email": "Optional, must contain @"
    })
    
    if errors:
        builder.with_message("Validation failed")
    elif warnings:
        builder.with_message("Validation completed with warnings")
    else:
        builder.with_message("All validation passed")
    
    return builder.build()

@demo_router.get("/patterns-summary/", response_model=Dict[str, Any])
async def demo_patterns_summary():
    """Provide a summary of all available response patterns"""
    
    patterns = {
        "basic_responses": {
            "success": "ResponseHandler.create_success_response()",
            "error": "ResponseHandler.create_error_response()",
            "warning": "ResponseHandler.create_warning_response()",
            "partial_success": "ResponseHandler.create_partial_success_response()"
        },
        "specialized_responses": {
            "query_result": "ResponseHandler.create_query_response()",
            "dataset_insights": "ResponseHandler.create_dataset_insights_response()",
            "tool_execution": "ResponseHandler.create_tool_execution_response()",
            "history": "ResponseHandler.create_history_response()"
        },
        "utility_functions": {
            "validation": "validate_and_extract_data()",
            "merging": "merge_responses()",
            "pagination": "create_paginated_response()",
            "timeout": "execute_with_timeout()"
        },
        "patterns": {
            "builder": "ResponseBuilder class for complex responses",
            "decorator": "@handle_service_response for service methods",
            "batch_processing": "Process multiple items and merge results",
            "validation": "Validate inputs and return appropriate responses"
        }
    }
    
    return ResponseHandler.create_success_response(
        data=patterns,
        message="Response handling patterns summary",
        response_type=ResponseType.GENERAL,
        metadata={
            "documentation": "Check app/core/response_utils.py for implementation details",
            "examples": "Use /demo/* endpoints to see patterns in action"
        }
    )
