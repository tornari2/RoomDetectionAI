"""
Async processor for managing asynchronous blueprint processing tasks.
"""

import json
import os
import boto3
from typing import Dict, Any
from botocore.exceptions import ClientError

from .status_manager import get_status_manager, StatusManagerError

# Initialize Lambda client
lambda_client = boto3.client('lambda')

# Environment variables
PROCESSING_LAMBDA_NAME = os.environ.get('PROCESSING_LAMBDA_NAME', 'room-detection-processor')


class AsyncProcessorError(Exception):
    """Custom exception for async processor errors."""
    pass


class AsyncProcessor:
    """Manages asynchronous processing tasks."""
    
    def __init__(self, processing_lambda_name: str = None):
        """
        Initialize async processor.
        
        Args:
            processing_lambda_name: Name of the Lambda function that processes images
        """
        self.processing_lambda_name = processing_lambda_name or PROCESSING_LAMBDA_NAME
        self.status_manager = get_status_manager()
    
    def submit_task(
        self,
        blueprint_id: str,
        s3_bucket: str,
        s3_key: str
    ) -> None:
        """
        Submit a new processing task.
        
        Args:
            blueprint_id: Unique blueprint identifier
            s3_bucket: S3 bucket name
            s3_key: S3 object key
        """
        try:
            # Create initial status
            self.status_manager.create_status(
                blueprint_id=blueprint_id,
                message="Blueprint uploaded. Processing started."
            )
            
            # Invoke processing Lambda asynchronously
            payload = {
                'blueprint_id': blueprint_id,
                's3_bucket': s3_bucket,
                's3_key': s3_key
            }
            
            lambda_client.invoke(
                FunctionName=self.processing_lambda_name,
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(payload)
            )
            
        except StatusManagerError as e:
            raise AsyncProcessorError(f"Failed to create status: {str(e)}")
        except ClientError as e:
            # Update status to failed if Lambda invocation fails
            try:
                self.status_manager.mark_failed(
                    blueprint_id=blueprint_id,
                    error='lambda_invocation_failed',
                    message=f"Failed to start processing: {str(e)}"
                )
            except:
                pass  # If status update fails, at least log the original error
            raise AsyncProcessorError(f"Failed to invoke processing Lambda: {str(e)}")
    
    def get_task_status(self, blueprint_id: str) -> Dict[str, Any]:
        """
        Get task status.
        
        Args:
            blueprint_id: Unique blueprint identifier
            
        Returns:
            Status dictionary
        """
        status = self.status_manager.get_status(blueprint_id)
        
        if not status:
            return {
                'blueprint_id': blueprint_id,
                'status': 'not_found',
                'message': f'Blueprint {blueprint_id} not found'
            }
        
        return status


# Singleton instance
_async_processor = None


def get_async_processor() -> AsyncProcessor:
    """Get singleton async processor instance."""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncProcessor()
    return _async_processor

