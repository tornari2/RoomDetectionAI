"""
Error handling middleware for API Gateway handlers.
Provides standardized error response formatting.
"""

import json
import traceback
from typing import Dict, Any, Callable


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    blueprint_id: str = None,
    details: str = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_code: Error code identifier
        message: Human-readable error message
        status_code: HTTP status code
        blueprint_id: Blueprint ID if applicable
        details: Additional error details
        
    Returns:
        API Gateway response format
    """
    error_body = {
        'error': error_code,
        'message': message
    }
    
    if blueprint_id:
        error_body['blueprint_id'] = blueprint_id
    
    if details:
        error_body['details'] = details
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(error_body)
    }


def error_handler_middleware(handler: Callable) -> Callable:
    """
    Middleware decorator to wrap handlers with error handling.
    
    Args:
        handler: Handler function to wrap
        
    Returns:
        Wrapped handler function
    """
    def wrapped_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            return handler(event, context)
        except ValueError as e:
            # Validation errors
            return create_error_response(
                error_code='validation_error',
                message=str(e),
                status_code=400
            )
        except FileNotFoundError as e:
            # File not found errors
            return create_error_response(
                error_code='file_not_found',
                message=str(e),
                status_code=404
            )
        except PermissionError as e:
            # Permission errors
            return create_error_response(
                error_code='permission_denied',
                message=str(e),
                status_code=403
            )
        except Exception as e:
            # Unexpected errors - log full traceback
            traceback.print_exc()
            return create_error_response(
                error_code='internal_error',
                message='An unexpected error occurred',
                status_code=500,
                details=str(e) if __debug__ else None
            )
    
    return wrapped_handler


# Common error responses
ERROR_RESPONSES = {
    'invalid_file_format': lambda details=None: create_error_response(
        error_code='invalid_file_format',
        message='File must be PNG or JPG format',
        status_code=400,
        details=details
    ),
    'file_too_large': lambda details=None: create_error_response(
        error_code='file_too_large',
        message='File size exceeds 50MB limit',
        status_code=413,
        details=details
    ),
    'blueprint_not_found': lambda blueprint_id: create_error_response(
        error_code='blueprint_not_found',
        message=f'Blueprint with ID {blueprint_id} not found',
        status_code=404,
        blueprint_id=blueprint_id
    ),
    'processing_failed': lambda blueprint_id, message, details=None: create_error_response(
        error_code='processing_failed',
        message=message or 'Unable to detect clear room boundaries',
        status_code=500,
        blueprint_id=blueprint_id,
        details=details
    )
}

