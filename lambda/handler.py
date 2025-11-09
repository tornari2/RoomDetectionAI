"""
Lambda function handler for room detection image processing.
Handles image preprocessing, SageMaker endpoint invocation, and response formatting.
"""

import json
import os
import base64
import time
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

try:
    # For local testing
    from utils.image_processor import preprocess_image, get_image_dimensions
    from utils.coordinate_transformer import transform_coordinates_to_normalized
    from utils.status_manager import get_status_manager
except ImportError:
    # For Lambda deployment (relative imports)
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from utils.image_processor import preprocess_image, get_image_dimensions
    from utils.coordinate_transformer import transform_coordinates_to_normalized
    from utils.status_manager import get_status_manager


# Initialize AWS clients
# AWS_REGION is automatically provided by Lambda runtime, use boto3's default session
sagemaker_runtime = boto3.client('sagemaker-runtime')
s3_client = boto3.client('s3')

# Environment variables
SAGEMAKER_ENDPOINT_NAME = os.environ.get('SAGEMAKER_ENDPOINT_NAME', 'room-detection-yolov8-endpoint')
S3_BUCKET = os.environ.get('S3_BUCKET', 'room-detection-ai-blueprints-dev')

# Initialize status manager
status_manager = get_status_manager()


class LambdaError(Exception):
    """Custom exception for Lambda function errors."""
    pass


def download_image_from_s3(bucket: str, key: str) -> bytes:
    """
    Download image from S3 bucket.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        Image bytes
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    except ClientError as e:
        raise LambdaError(f"Failed to download image from S3: {str(e)}")


def invoke_sagemaker_endpoint(image_bytes: bytes) -> Dict[str, Any]:
    """
    Invoke SageMaker endpoint with preprocessed image.
    
    Args:
        image_bytes: Preprocessed image bytes
        
    Returns:
        SageMaker endpoint response as dictionary
    """
    try:
        # Encode image as base64 for JSON payload
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        payload = json.dumps({'image': image_base64})
        
        # Invoke endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT_NAME,
            ContentType='application/json',
            Accept='application/json',
            Body=payload
        )
        
        # Parse response
        response_body = response['Body'].read().decode('utf-8')
        return json.loads(response_body)
        
    except ClientError as e:
        raise LambdaError(f"Failed to invoke SageMaker endpoint: {str(e)}")
    except json.JSONDecodeError as e:
        raise LambdaError(f"Failed to parse SageMaker response: {str(e)}")


def process_image(image_bytes: bytes, blueprint_id: str) -> Dict[str, Any]:
    """
    Main image processing pipeline.
    
    Args:
        image_bytes: Raw image bytes
        blueprint_id: Unique identifier for the blueprint
        
    Returns:
        Formatted response dictionary
    """
    start_time = time.time()
    
    try:
        # Get original image dimensions
        original_width, original_height = get_image_dimensions(image_bytes)
        
        # Preprocess image (resize to 640x640)
        preprocessed_image = preprocess_image(image_bytes, target_size=(640, 640))
        
        # Convert PIL Image to bytes for SageMaker
        from PIL import Image
        import io
        img_byte_arr = io.BytesIO()
        preprocessed_image.save(img_byte_arr, format='PNG')
        preprocessed_bytes = img_byte_arr.getvalue()
        
        # Invoke SageMaker endpoint
        sagemaker_response = invoke_sagemaker_endpoint(preprocessed_bytes)
        
        # Extract results
        detected_rooms = sagemaker_response.get('detected_rooms', [])
        processing_time_ms = sagemaker_response.get('processing_time_ms', 0)
        
        # Calculate total processing time
        total_time_ms = int((time.time() - start_time) * 1000)
        
        # Update status to completed
        status_manager.mark_completed(
            blueprint_id=blueprint_id,
            processing_time_ms=total_time_ms,
            detected_rooms=detected_rooms,
            message="Processing completed successfully"
        )
        
        # Format response according to API spec
        response = {
            'blueprint_id': blueprint_id,
            'status': 'completed',
            'processing_time_ms': total_time_ms,
            'detected_rooms': detected_rooms
        }
        
        return response
        
    except Exception as e:
        # Update status to failed
        try:
            status_manager.mark_failed(
                blueprint_id=blueprint_id,
                error='processing_error',
                message=str(e)
            )
        except:
            pass  # If status update fails, continue with exception
        
        raise LambdaError(f"Image processing failed: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    Expected event structure:
    {
        "blueprint_id": "bp_abc123",
        "s3_bucket": "room-detection-ai-blueprints-dev",
        "s3_key": "uploads/bp_abc123/image.png"
    }
    
    Returns:
        API response dictionary
    """
    try:
        # Extract event parameters
        blueprint_id = event.get('blueprint_id')
        s3_bucket = event.get('s3_bucket', S3_BUCKET)
        s3_key = event.get('s3_key')
        
        # Validate required parameters
        if not blueprint_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'blueprint_id': blueprint_id or 'unknown',
                    'status': 'failed',
                    'error': 'missing_blueprint_id',
                    'message': 'blueprint_id is required'
                })
            }
        
        if not s3_key:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'blueprint_id': blueprint_id,
                    'status': 'failed',
                    'error': 'missing_s3_key',
                    'message': 's3_key is required'
                })
            }
        
        # Update status to processing
        try:
            status_manager.update_status(
                blueprint_id=blueprint_id,
                status='processing',
                message='Downloading image from S3...'
            )
        except:
            pass  # Continue even if status update fails
        
        # Download image from S3
        image_bytes = download_image_from_s3(s3_bucket, s3_key)
        
        # Update status
        try:
            status_manager.update_status(
                blueprint_id=blueprint_id,
                status='processing',
                message='Processing image with SageMaker...'
            )
        except:
            pass
        
        # Process image
        result = process_image(image_bytes, blueprint_id)
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except LambdaError as e:
        # Return error response
        blueprint_id = event.get('blueprint_id', 'unknown')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'blueprint_id': blueprint_id,
                'status': 'failed',
                'error': 'processing_error',
                'message': str(e)
            })
        }
        
    except Exception as e:
        # Unexpected error
        blueprint_id = event.get('blueprint_id', 'unknown')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'blueprint_id': blueprint_id,
                'status': 'failed',
                'error': 'internal_error',
                'message': f'An unexpected error occurred: {str(e)}'
            })
        }

