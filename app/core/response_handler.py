from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
import traceback
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ResponseStatus(Enum):
    """Response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL_SUCCESS = "partial_success"

class ResponseType(Enum):
    """Response type enumeration"""
    QUERY_RESULT = "query_result"
    DATASET_INSIGHT = "dataset_insight"
    TOOL_EXECUTION = "tool_execution"
    QUERY_HISTORY = "query_history"
    VALIDATION = "validation"
    VALIDATION_ERROR = "validation_error"
    VALIDATION_SUCCESS = "validation_success"
    AGENT_SUGGESTIONS = "agent_suggestions" 
    GENERAL = "general"

class HTTPStatusCode(Enum):
    """HTTP status codes for API responses"""
    # Success codes
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    
    # Client error codes
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # Server error codes
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504

class ResponseHandler:
    """Centralized response handler for consistent API responses"""

    @staticmethod
    def create_success_response(
        data: Any = None,
        message: str = "Operation completed successfully",
        response_type: ResponseType = ResponseType.GENERAL,
        metadata: Optional[Dict[str, Any]] = None,
        status_code: HTTPStatusCode = HTTPStatusCode.OK
    ) -> Dict[str, Any]:
        """Create a standardized success response"""
        response = {
            "status": ResponseStatus.SUCCESS.value,
            "status_code": status_code.value,
            "message": message,
            "type": response_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": metadata or {}
        }
        
        logger.debug(f"Success response created: {response_type.value} (HTTP {status_code.value})")
        return response
    
    @staticmethod
    def create_error_response(
        error: Union[str, Exception],
        message: str = "An error occurred",
        response_type: ResponseType = ResponseType.GENERAL,
        include_traceback: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        status_code: HTTPStatusCode = HTTPStatusCode.INTERNAL_SERVER_ERROR
    ) -> Dict[str, Any]:
        """Create a standardized error response"""
        
        error_details = {
            "error_message": str(error),
            "error_type": type(error).__name__ if isinstance(error, Exception) else "CustomError"
        }
        
        if include_traceback and isinstance(error, Exception):
            error_details["traceback"] = traceback.format_exc()
        
        response = {
            "status": ResponseStatus.ERROR.value,
            "status_code": status_code.value,
            "message": message,
            "type": response_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": None,
            "error": error_details,
            "metadata": metadata or {}
        }
        
        logger.error(f"Error response created: {message} - {error} (HTTP {status_code.value})")
        return response
    
    @staticmethod
    def create_warning_response(
        data: Any = None,
        message: str = "Operation completed with warnings",
        warnings: List[str] = None,
        response_type: ResponseType = ResponseType.GENERAL,
        metadata: Optional[Dict[str, Any]] = None,
        status_code: HTTPStatusCode = HTTPStatusCode.OK
    ) -> Dict[str, Any]:
        """Create a standardized warning response"""
        
        response = {
            "status": ResponseStatus.WARNING.value,
            "status_code": status_code.value,
            "message": message,
            "type": response_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "warnings": warnings or [],
            "metadata": metadata or {}
        }
        
        logger.warning(f"Warning response created: {message} (HTTP {status_code.value})")
        return response
    
    @staticmethod
    def create_partial_success_response(
        data: Any = None,
        message: str = "Operation partially completed",
        warnings: List[str] = None,
        response_type: ResponseType = ResponseType.GENERAL,
        metadata: Optional[Dict[str, Any]] = None,
        status_code: HTTPStatusCode = HTTPStatusCode.OK
    ) -> Dict[str, Any]:
        """Create a standardized partial success response"""
        
        response = {
            "status": ResponseStatus.PARTIAL_SUCCESS.value,
            "status_code": status_code.value,
            "message": message,
            "type": response_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "warnings": warnings or [],
            "metadata": metadata or {}
        }
        
        logger.info(f"Partial success response created: {message} (HTTP {status_code.value})")
        return response
    
    @staticmethod
    def create_query_response(
        result: Any,
        execution_time: float,
        query: str,
        dataset_id: int,
        profile_name: str = None,
        success: bool = True,
        error: str = None
    ) -> Dict[str, Any]:
        """Create a specialized response for query results"""
        
        metadata = {
            "execution_time_seconds": execution_time,
            "query": query,
            "dataset_id": dataset_id,
            "profile_name": profile_name,
            "result_type": type(result).__name__ if result else None
        }
        
        if success:
            return ResponseHandler.create_success_response(
                data=result,
                message=f"Query executed successfully in {execution_time:.2f}s",
                response_type=ResponseType.QUERY_RESULT,
                metadata=metadata
            )
        else:
            return ResponseHandler.create_error_response(
                error=error or "Query execution failed",
                message="Failed to execute query",
                response_type=ResponseType.QUERY_RESULT,
                metadata=metadata
            )
    
    @staticmethod
    def create_dataset_insights_response(
        insights: Dict[str, Any],
        dataset_id: int,
        profile_name: str,
        success: bool = True,
        error: str = None
    ) -> Dict[str, Any]:
        """Create a specialized response for dataset insights"""
        
        metadata = {
            "dataset_id": dataset_id,
            "profile_name": profile_name,
            "insights_count": len(insights) if insights else 0
        }
        
        if success:
            return ResponseHandler.create_success_response(
                data=insights,
                message="Dataset insights generated successfully",
                response_type=ResponseType.DATASET_INSIGHT,
                metadata=metadata
            )
        else:
            return ResponseHandler.create_error_response(
                error=error or "Failed to generate insights",
                message="Dataset insights generation failed",
                response_type=ResponseType.DATASET_INSIGHT,
                metadata=metadata
            )
    
    @staticmethod
    def create_validation_error_response(
        errors: List[str],
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, List[str]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a specialized validation error response"""
        
        error_details = {
            "error_message": "; ".join(errors),
            "error_type": "ValidationError",
            "errors": errors,
            "field_errors": field_errors or {}
        }
        
        response = {
            "status": ResponseStatus.ERROR.value,
            "status_code": HTTPStatusCode.BAD_REQUEST.value,
            "message": message,
            "type": ResponseType.VALIDATION.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": None,
            "error": error_details,
            "metadata": metadata or {}
        }
        
        logger.error(f"Validation error response created: {message} (HTTP 400)")
        return response
    
    @staticmethod
    def create_not_found_response(
        resource: str,
        resource_id: Any = None,
        message: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a standardized not found response"""
        
        if not message:
            if resource_id:
                message = f"{resource} with ID {resource_id} not found"
            else:
                message = f"{resource} not found"
        
        error_details = {
            "error_message": message,
            "error_type": "NotFoundError",
            "resource": resource,
            "resource_id": resource_id
        }
        
        response = {
            "status": ResponseStatus.ERROR.value,
            "status_code": HTTPStatusCode.NOT_FOUND.value,
            "message": message,
            "type": ResponseType.GENERAL.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": None,
            "error": error_details,
            "metadata": metadata or {}
        }
        
        logger.error(f"Not found response created: {message} (HTTP 404)")
        return response
    
    @staticmethod
    def validate_response_format(response: Dict[str, Any]) -> bool:
        """Validate that a response follows the expected format"""
        required_fields = ["status", "message", "type", "timestamp"]
        
        for field in required_fields:
            if field not in response:
                logger.error(f"Response missing required field: {field}")
                return False
        
        if response["status"] not in [status.value for status in ResponseStatus]:
            logger.error(f"Invalid response status: {response['status']}")
            return False
        
        return True
    
    @staticmethod
    def is_success(response: Dict[str, Any]) -> bool:
        """Check if a response indicates success"""
        return response.get("status") == ResponseStatus.SUCCESS.value
    
    @staticmethod
    def is_error(response: Dict[str, Any]) -> bool:
        """Check if a response indicates an error"""
        return response.get("status") == ResponseStatus.ERROR.value
    
    @staticmethod
    def get_error_message(response: Dict[str, Any]) -> Optional[str]:
        """Extract error message from response"""
        if ResponseHandler.is_error(response):
            error_info = response.get("error", {})
            return error_info.get("error_message", response.get("message"))
        return None
    
    @staticmethod
    def extract_data_safely(response: Dict[str, Any]) -> Any:
        """Extract data from response safely"""
        if ResponseHandler.is_success(response):
            return response.get("data", {})
        return None
    
    @staticmethod
    def create_history_response(
        queries: List[Dict[str, Any]],
        dataset_id: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a query history response"""
        if success and error is None:
            return ResponseHandler.create_success_response(
                data=queries,
                message=f"Retrieved {len(queries)} query records",
                response_type=ResponseType.QUERY_HISTORY,
                metadata={
                    "query_count": len(queries),
                    "dataset_id": dataset_id
                }
            )
        else:
            return ResponseHandler.create_error_response(
                error=error,
                message="Failed to retrieve query history",
                response_type=ResponseType.QUERY_HISTORY
            )
