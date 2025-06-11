"""
Response handling utilities and patterns for the PandasAI Q&A System
This module provides common patterns and utilities for working with the ResponseHandler
"""

from typing import Any, Dict, List, Optional, Callable, Union
from functools import wraps
from app.core.response_handler import ResponseHandler, ResponseType, ResponseStatus, HTTPStatusCode
from app.core.logging_config import get_logger
import time
import asyncio

logger = get_logger(__name__)

def handle_service_response(
    response_type: ResponseType = ResponseType.GENERAL,
    include_execution_time: bool = False,
    log_result: bool = True
):
    """Decorator for service methods to standardize response handling"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time() if include_execution_time else None
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time if start_time else None
                
                if log_result:
                    logger.info(f"Service method {func.__name__} completed successfully")
                
                # If the result is already a response dict, return it as-is
                if isinstance(result, dict) and "status" in result:
                    if execution_time and "metadata" in result:
                        result["metadata"]["execution_time_seconds"] = execution_time
                    return result
                
                # Otherwise, wrap in success response
                metadata = {"execution_time_seconds": execution_time} if execution_time else None
                return ResponseHandler.create_success_response(
                    data=result,
                    message=f"Operation {func.__name__} completed successfully",
                    response_type=response_type,
                    metadata=metadata
                )
                
            except Exception as e:
                execution_time = time.time() - start_time if start_time else None
                logger.error(f"Error in service method {func.__name__}: {e}")
                
                metadata = {"execution_time_seconds": execution_time} if execution_time else None
                return ResponseHandler.create_error_response(
                    error=e,
                    message=f"Operation {func.__name__} failed",
                    response_type=response_type,
                    metadata=metadata
                )
        
        return wrapper
    return decorator

def validate_and_extract_data(response: Dict[str, Any]) -> tuple[bool, Any, Optional[str]]:
    """
    Validate response and extract data safely
    Returns: (is_success, data, error_message)
    """
    if not ResponseHandler.validate_response_format(response):
        return False, None, "Invalid response format"
    
    is_success = ResponseHandler.is_success(response)
    data = ResponseHandler.extract_data_safely(response) if is_success else None
    error_message = ResponseHandler.get_error_message(response) if not is_success else None
    
    return is_success, data, error_message

def merge_responses(responses: List[Dict[str, Any]], operation_name: str = "batch_operation") -> Dict[str, Any]:
    """
    Merge multiple responses into a single response
    Useful for batch operations or combining results from multiple services
    """
    try:
        if not responses:
            return ResponseHandler.create_error_response(
                error="No responses to merge",
                message="Batch operation received no responses",
                response_type=ResponseType.GENERAL
            )
        
        successful_responses = []
        failed_responses = []
        warnings = []
        
        for i, response in enumerate(responses):
            if not ResponseHandler.validate_response_format(response):
                failed_responses.append({
                    "index": i,
                    "error": "Invalid response format",
                    "response": response
                })
                continue
            
            if ResponseHandler.is_success(response):
                successful_responses.append({
                    "index": i,
                    "data": ResponseHandler.extract_data_safely(response),
                    "metadata": response.get("metadata", {})
                })
            elif response.get("status") == ResponseStatus.WARNING.value:
                warnings.extend(response.get("warnings", []))
                successful_responses.append({
                    "index": i,
                    "data": ResponseHandler.extract_data_safely(response),
                    "metadata": response.get("metadata", {}),
                    "warnings": response.get("warnings", [])
                })
            else:
                failed_responses.append({
                    "index": i,
                    "error": ResponseHandler.get_error_message(response),
                    "response": response
                })
        
        total_operations = len(responses)
        successful_count = len(successful_responses)
        failed_count = len(failed_responses)
        
        merged_data = {
            "total_operations": total_operations,
            "successful_operations": successful_count,
            "failed_operations": failed_count,
            "success_rate": successful_count / total_operations if total_operations > 0 else 0,
            "successful_results": successful_responses,
            "failed_results": failed_responses
        }
        
        # Determine response type based on results
        if failed_count == 0:
            if warnings:
                return ResponseHandler.create_warning_response(
                    data=merged_data,
                    message=f"{operation_name} completed with warnings",
                    warnings=warnings,
                    response_type=ResponseType.GENERAL
                )
            else:
                return ResponseHandler.create_success_response(
                    data=merged_data,
                    message=f"{operation_name} completed successfully",
                    response_type=ResponseType.GENERAL
                )
        elif successful_count == 0:
            return ResponseHandler.create_error_response(
                error="All operations failed",
                message=f"{operation_name} failed completely",
                response_type=ResponseType.GENERAL,
                metadata={"failed_operations": failed_responses}
            )
        else:
            return ResponseHandler.create_partial_success_response(
                data=merged_data,
                message=f"{operation_name} partially completed",
                warnings=[f"{failed_count} out of {total_operations} operations failed"],
                response_type=ResponseType.GENERAL
            )
            
    except Exception as e:
        logger.error(f"Error merging responses: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to merge responses",
            response_type=ResponseType.GENERAL
        )

def create_paginated_response(
    data: List[Any], 
    page: int = 1, 
    page_size: int = 10,
    total_count: Optional[int] = None
) -> Dict[str, Any]:
    """Create a paginated response"""
    try:
        if not isinstance(data, list):
            raise ValueError("Data must be a list for pagination")
        
        total_count = total_count or len(data)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_data = data[start_index:end_index]
        
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        pagination_info = {
            "current_page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_count": total_count,
            "has_next": has_next,
            "has_previous": has_previous,
            "items_on_page": len(paginated_data)
        }
        
        return ResponseHandler.create_success_response(
            data=paginated_data,
            message=f"Retrieved page {page} of {total_pages}",
            response_type=ResponseType.GENERAL,
            metadata={"pagination": pagination_info}
        )
        
    except Exception as e:
        logger.error(f"Error creating paginated response: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message="Failed to create paginated response",
            response_type=ResponseType.GENERAL
        )

async def execute_with_timeout(
    operation: Callable,
    timeout_seconds: float = 30.0,
    operation_name: str = "operation"
) -> Dict[str, Any]:
    """Execute an operation with timeout and proper response handling"""
    try:
        logger.debug(f"Executing {operation_name} with timeout {timeout_seconds}s")
        
        result = await asyncio.wait_for(operation(), timeout=timeout_seconds)
        
        return ResponseHandler.create_success_response(
            data=result,
            message=f"{operation_name} completed within timeout",
            response_type=ResponseType.GENERAL,
            metadata={"timeout_seconds": timeout_seconds}
        )
        
    except asyncio.TimeoutError:
        logger.error(f"{operation_name} timed out after {timeout_seconds} seconds")
        return ResponseHandler.create_error_response(
            error=f"Operation timed out after {timeout_seconds} seconds",
            message=f"{operation_name} exceeded timeout limit",
            response_type=ResponseType.GENERAL,
            metadata={"timeout_seconds": timeout_seconds}
        )
    except Exception as e:
        logger.error(f"Error executing {operation_name}: {e}")
        return ResponseHandler.create_error_response(
            error=e,
            message=f"{operation_name} failed",
            response_type=ResponseType.GENERAL,
            metadata={"timeout_seconds": timeout_seconds}
        )

def get_http_status_from_response(response: Dict[str, Any]) -> int:
    """Extract HTTP status code from response"""
    return response.get("status_code", HTTPStatusCode.OK.value)

def is_client_error(response: Dict[str, Any]) -> bool:
    """Check if response indicates a client error (4xx)"""
    status_code = get_http_status_from_response(response)
    return 400 <= status_code < 500

def is_server_error(response: Dict[str, Any]) -> bool:
    """Check if response indicates a server error (5xx)"""
    status_code = get_http_status_from_response(response)
    return 500 <= status_code < 600

def create_response_with_appropriate_status(
    is_success: bool,
    data: Any = None,
    message: str = None,
    errors: List[str] = None,
    warnings: List[str] = None,
    response_type: ResponseType = ResponseType.GENERAL,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create response with appropriate HTTP status code based on content"""
    
    if errors:
        # Determine appropriate error status code
        if any("not found" in error.lower() for error in errors):
            status_code = HTTPStatusCode.NOT_FOUND
        elif any("unauthorized" in error.lower() or "permission" in error.lower() for error in errors):
            status_code = HTTPStatusCode.UNAUTHORIZED
        elif any("validation" in error.lower() or "invalid" in error.lower() for error in errors):
            status_code = HTTPStatusCode.BAD_REQUEST
        else:
            status_code = HTTPStatusCode.INTERNAL_SERVER_ERROR
        
        return ResponseHandler.create_error_response(
            error="; ".join(errors),
            message=message or "Operation failed",
            response_type=response_type,
            metadata=metadata,
            status_code=status_code
        )
    
    elif warnings:
        return ResponseHandler.create_warning_response(
            data=data,
            message=message or "Operation completed with warnings",
            warnings=warnings,
            response_type=response_type,
            metadata=metadata,
            status_code=HTTPStatusCode.OK
        )
    
    else:
        # Determine success status code
        if response_type == ResponseType.GENERAL and data and isinstance(data, dict) and data.get("created"):
            status_code = HTTPStatusCode.CREATED
        else:
            status_code = HTTPStatusCode.OK
        
        return ResponseHandler.create_success_response(
            data=data,
            message=message or "Operation completed successfully",
            response_type=response_type,
            metadata=metadata,
            status_code=status_code
        )

class ResponseBuilder:
    """Builder class for creating complex responses"""
    
    def __init__(self, response_type: ResponseType = ResponseType.GENERAL):
        self.response_type = response_type
        self._data = None
        self._message = None
        self._metadata = {}
        self._warnings = []
        self._errors = []
    
    def with_data(self, data: Any) -> 'ResponseBuilder':
        """Add data to the response"""
        self._data = data
        return self
    
    def with_message(self, message: str) -> 'ResponseBuilder':
        """Add message to the response"""
        self._message = message
        return self
    
    def with_metadata(self, key: str, value: Any) -> 'ResponseBuilder':
        """Add metadata to the response"""
        self._metadata[key] = value
        return self
    
    def with_warning(self, warning: str) -> 'ResponseBuilder':
        """Add warning to the response"""
        self._warnings.append(warning)
        return self
    
    def with_error(self, error: Union[str, Exception]) -> 'ResponseBuilder':
        """Add error to the response"""
        self._errors.append(str(error))
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the final response"""
        if self._errors:
            return ResponseHandler.create_error_response(
                error="; ".join(self._errors),
                message=self._message or "Operation failed",
                response_type=self.response_type,
                metadata=self._metadata
            )
        elif self._warnings:
            return ResponseHandler.create_warning_response(
                data=self._data,
                message=self._message or "Operation completed with warnings",
                warnings=self._warnings,
                response_type=self.response_type,
                metadata=self._metadata
            )
        else:
            return ResponseHandler.create_success_response(
                data=self._data,
                message=self._message or "Operation completed successfully",
                response_type=self.response_type,
                metadata=self._metadata
            )

class HTTPStatusAwareResponseBuilder(ResponseBuilder):
    """Extended ResponseBuilder with HTTP status code awareness"""
    
    def __init__(self, response_type: ResponseType = ResponseType.GENERAL):
        super().__init__(response_type)
        self._status_code = None
    
    def with_status_code(self, status_code: HTTPStatusCode) -> 'HTTPStatusAwareResponseBuilder':
        """Set specific HTTP status code"""
        self._status_code = status_code
        return self
    
    def with_created_status(self) -> 'HTTPStatusAwareResponseBuilder':
        """Set HTTP 201 Created status"""
        self._status_code = HTTPStatusCode.CREATED
        return self
    
    def with_not_found_status(self) -> 'HTTPStatusAwareResponseBuilder':
        """Set HTTP 404 Not Found status"""
        self._status_code = HTTPStatusCode.NOT_FOUND
        return self
    
    def with_bad_request_status(self) -> 'HTTPStatusAwareResponseBuilder':
        """Set HTTP 400 Bad Request status"""
        self._status_code = HTTPStatusCode.BAD_REQUEST
        return self
    
    def with_unauthorized_status(self) -> 'HTTPStatusAwareResponseBuilder':
        """Set HTTP 401 Unauthorized status"""
        self._status_code = HTTPStatusCode.UNAUTHORIZED
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the final response with appropriate HTTP status code"""
        
        # Determine default status code if not explicitly set
        if self._status_code is None:
            if self._errors:
                if any("not found" in str(error).lower() for error in self._errors):
                    self._status_code = HTTPStatusCode.NOT_FOUND
                elif any("unauthorized" in str(error).lower() for error in self._errors):
                    self._status_code = HTTPStatusCode.UNAUTHORIZED
                elif any("validation" in str(error).lower() or "invalid" in str(error).lower() for error in self._errors):
                    self._status_code = HTTPStatusCode.BAD_REQUEST
                else:
                    self._status_code = HTTPStatusCode.INTERNAL_SERVER_ERROR
            elif self._warnings:
                self._status_code = HTTPStatusCode.OK
            else:
                # Check if this looks like a creation operation
                if (self._data and isinstance(self._data, dict) and 
                    any(key in self._data for key in ["id", "created_at", "created"])):
                    self._status_code = HTTPStatusCode.CREATED
                else:
                    self._status_code = HTTPStatusCode.OK
        
        # Build response using parent logic
        if self._errors:
            return ResponseHandler.create_error_response(
                error="; ".join(self._errors),
                message=self._message or "Operation failed",
                response_type=self.response_type,
                metadata=self._metadata,
                status_code=self._status_code
            )
        elif self._warnings:
            return ResponseHandler.create_warning_response(
                data=self._data,
                message=self._message or "Operation completed with warnings",
                warnings=self._warnings,
                response_type=self.response_type,
                metadata=self._metadata,
                status_code=self._status_code
            )
        else:
            return ResponseHandler.create_success_response(
                data=self._data,
                message=self._message or "Operation completed successfully",
                response_type=self.response_type,
                metadata=self._metadata,
                status_code=self._status_code
            )

# Usage examples and patterns
RESPONSE_PATTERNS = {
    "data_processing": {
        "description": "Pattern for data processing operations",
        "example": """
        @handle_service_response(ResponseType.QUERY_RESULT, include_execution_time=True)
        async def process_data(self, data):
            # Process data here
            return processed_data
        """
    },
    "validation": {
        "description": "Pattern for validation operations",
        "example": """
        def validate_input(self, input_data):
            builder = ResponseBuilder(ResponseType.VALIDATION)
            
            if not input_data:
                builder.with_error("Input data is empty")
            
            if len(input_data) > 1000:
                builder.with_warning("Input data is very large")
            
            return builder.with_data(input_data).build()
        """
    },
    "batch_operations": {
        "description": "Pattern for batch operations",
        "example": """
        async def process_batch(self, items):
            responses = []
            for item in items:
                response = await self.process_single_item(item)
                responses.append(response)
            
            return merge_responses(responses, "batch_processing")
        """
    }
}
