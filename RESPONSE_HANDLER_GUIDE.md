# Response Handler System Documentation

## Overview

The PandasAI Q&A System uses a centralized response handling system to ensure consistency, maintainability, and better error handling across all API endpoints and services.

## Core Components

### 1. ResponseHandler (`app/core/response_handler.py`)

The main class that provides static methods for creating standardized responses.

#### Response Structure

All responses follow this structure:

```json
{
  "status": "success|error|warning|partial_success",
  "message": "Human-readable message",
  "type": "query_result|dataset_insight|tool_execution|...",
  "timestamp": "2025-06-11T10:30:00Z",
  "data": {}, // Actual response data
  "metadata": {}, // Additional information
  "error": {}, // Error details (if applicable)
  "warnings": [] // Warning messages (if applicable)
}
```

#### Basic Response Methods

```python
from app.core.response_handler import ResponseHandler, ResponseType

# Success response
response = ResponseHandler.create_success_response(
    data={"result": "processed"},
    message="Operation completed successfully",
    response_type=ResponseType.GENERAL
)

# Error response
response = ResponseHandler.create_error_response(
    error="Database connection failed",
    message="Unable to process request",
    response_type=ResponseType.GENERAL
)

# Warning response
response = ResponseHandler.create_warning_response(
    data={"processed": 95, "skipped": 5},
    message="Processing completed with warnings",
    warnings=["5 items were skipped due to invalid format"]
)
```

#### Specialized Response Methods

```python
# Query result response
response = ResponseHandler.create_query_response(
    result=query_result,
    execution_time=2.5,
    query="SELECT * FROM sales",
    dataset_id=123,
    profile_name="sales_analyst",
    success=True
)

# Dataset insights response
response = ResponseHandler.create_dataset_insights_response(
    insights=insights_data,
    dataset_id=123,
    profile_name="general_analyst",
    success=True
)
```

### 2. Response Utilities (`app/core/response_utils.py`)

Utility functions and patterns for advanced response handling.

#### Service Method Decorator

```python
from app.core.response_utils import handle_service_response

class MyService:
    @handle_service_response(ResponseType.GENERAL, include_execution_time=True)
    async def process_data(self, data):
        # Your processing logic here
        return processed_data
```

#### Response Builder Pattern

```python
from app.core.response_utils import ResponseBuilder

builder = ResponseBuilder(ResponseType.VALIDATION)
builder.with_data({"validated_field": value})
builder.with_message("Validation completed")
builder.with_metadata("validation_rules", rules)

if has_warnings:
    builder.with_warning("Some fields were auto-corrected")

if has_errors:
    builder.with_error("Required field missing")

response = builder.build()
```

#### Batch Processing

```python
from app.core.response_utils import merge_responses

responses = []
for item in batch_items:
    response = await process_single_item(item)
    responses.append(response)

merged_response = merge_responses(responses, "batch_processing")
```

#### Pagination

```python
from app.core.response_utils import create_paginated_response

paginated_response = create_paginated_response(
    data=all_items,
    page=1,
    page_size=10,
    total_count=100
)
```

## Service Implementation Patterns

### 1. Basic Service Method

```python
class QueryService:
    async def process_query(self, question: str, dataset_id: int) -> Dict[str, Any]:
        try:
            start_time = time.time()
            
            # Process the query
            result = await self.execute_query(question, dataset_id)
            execution_time = time.time() - start_time
            
            return ResponseHandler.create_query_response(
                result=result,
                execution_time=execution_time,
                query=question,
                dataset_id=dataset_id,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query processing failed: {e}")
            
            return ResponseHandler.create_query_response(
                result=None,
                execution_time=execution_time,
                query=question,
                dataset_id=dataset_id,
                success=False,
                error=str(e)
            )
```

### 2. Service with Validation

```python
class DatasetService:
    async def create_dataset(self, name: str, description: str = None) -> Dict[str, Any]:
        try:
            # Validate inputs
            if not name or not name.strip():
                return ResponseHandler.create_error_response(
                    error="Dataset name cannot be empty",
                    message="Validation failed",
                    response_type=ResponseType.VALIDATION
                )
            
            # Create dataset
            dataset = Dataset(name=name.strip(), description=description)
            self.db.add(dataset)
            self.db.commit()
            
            return ResponseHandler.create_success_response(
                data={"id": dataset.id, "name": dataset.name},
                message="Dataset created successfully"
            )
            
        except Exception as e:
            self.db.rollback()
            return ResponseHandler.create_error_response(
                error=e,
                message="Failed to create dataset"
            )
```

## Route Implementation Patterns

### 1. Basic Route

```python
@router.post("/process/", response_model=Dict[str, Any])
async def process_data(
    request: ProcessRequest,
    db: Session = Depends(get_db)
):
    try:
        service = DataService(db)
        return await service.process_data(request.data)
        
    except Exception as e:
        logger.error(f"Unexpected error in route: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Unexpected error occurred",
            response_type=ResponseType.GENERAL
        )
```

### 2. Route with Validation

```python
@router.post("/query/", response_model=Dict[str, Any])
async def process_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db)
):
    try:
        service = QueryService(db)
        
        # Validate parameters
        validation_result = await service.validate_query_parameters(
            question=query_request.question,
            dataset_id=query_request.dataset_id
        )
        
        if not ResponseHandler.is_success(validation_result):
            return validation_result
        
        # Process the query
        return await service.process_query(
            question=query_request.question,
            dataset_id=query_request.dataset_id
        )
        
    except Exception as e:
        return ResponseHandler.create_error_response(
            error=e,
            message="Query processing failed",
            response_type=ResponseType.QUERY_RESULT
        )
```

## Response Validation and Extraction

### Validating Responses

```python
from app.core.response_utils import validate_and_extract_data

response = await some_service_call()
is_success, data, error_message = validate_and_extract_data(response)

if is_success:
    # Use the data
    print(f"Success: {data}")
else:
    # Handle the error
    print(f"Error: {error_message}")
```

### Checking Response Status

```python
if ResponseHandler.is_success(response):
    data = ResponseHandler.extract_data_safely(response)
    # Process success case
elif ResponseHandler.is_error(response):
    error_msg = ResponseHandler.get_error_message(response)
    # Handle error case
```

## Demo Endpoints

The system includes comprehensive demo endpoints to showcase all response patterns:

- `GET /api/v1/demo/response-format/` - Basic response formats
- `GET /api/v1/demo/response-builder/` - ResponseBuilder pattern
- `GET /api/v1/demo/batch-processing/` - Batch processing with merge
- `GET /api/v1/demo/pagination/` - Paginated responses
- `GET /api/v1/demo/timeout-demo/` - Timeout handling
- `GET /api/v1/demo/validation-patterns/` - Validation patterns
- `GET /api/v1/demo/service-integration/` - Service integration
- `GET /api/v1/demo/patterns-summary/` - All patterns summary

## Best Practices

### 1. Always Use Response Handler

❌ **Don't do this:**
```python
async def get_data():
    try:
        data = fetch_data()
        return {"data": data, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

✅ **Do this:**
```python
async def get_data():
    try:
        data = fetch_data()
        return ResponseHandler.create_success_response(
            data=data,
            message="Data retrieved successfully"
        )
    except Exception as e:
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to retrieve data"
        )
```

### 2. Include Execution Time for Performance Monitoring

```python
async def process_heavy_operation():
    start_time = time.time()
    try:
        result = await heavy_operation()
        execution_time = time.time() - start_time
        
        return ResponseHandler.create_success_response(
            data=result,
            message="Operation completed",
            metadata={"execution_time_seconds": execution_time}
        )
    except Exception as e:
        execution_time = time.time() - start_time
        return ResponseHandler.create_error_response(
            error=e,
            message="Operation failed",
            metadata={"execution_time_seconds": execution_time}
        )
```

### 3. Use Appropriate Response Types

```python
# For query operations
ResponseType.QUERY_RESULT

# For dataset insights
ResponseType.DATASET_INSIGHT  

# For tool execution
ResponseType.TOOL_EXECUTION

# For validation
ResponseType.VALIDATION

# For history/listing
ResponseType.QUERY_HISTORY

# For general operations
ResponseType.GENERAL
```

### 4. Provide Meaningful Messages

❌ **Don't do this:**
```python
ResponseHandler.create_error_response(error="Error", message="Failed")
```

✅ **Do this:**
```python
ResponseHandler.create_error_response(
    error="Database connection timeout after 30 seconds",
    message="Unable to process query due to database connectivity issues"
)
```

### 5. Use Metadata for Additional Context

```python
ResponseHandler.create_success_response(
    data=query_result,
    message="Query executed successfully",
    metadata={
        "execution_time_seconds": 2.5,
        "rows_returned": 150,
        "query_complexity": "medium",
        "cache_used": False
    }
)
```

## Testing Response Handlers

```python
import pytest
from app.core.response_handler import ResponseHandler, ResponseType

def test_success_response():
    response = ResponseHandler.create_success_response(
        data={"test": "data"},
        message="Test successful"
    )
    
    assert response["status"] == "success"
    assert response["data"]["test"] == "data"
    assert "timestamp" in response

def test_error_response():
    response = ResponseHandler.create_error_response(
        error="Test error",
        message="Test failed"
    )
    
    assert response["status"] == "error"
    assert response["error"]["error_message"] == "Test error"
    assert response["data"] is None
```

## Migration Guide

If you have existing endpoints that don't use the response handler:

1. Update service methods to return response dictionaries instead of raw data
2. Update route handlers to use `response_model=Dict[str, Any]`
3. Remove HTTPException raises and return error responses instead
4. Add proper logging and execution time tracking
5. Test all endpoints to ensure they return the expected format

The response handler system provides consistency, better error handling, and improved maintainability across the entire application.
