"""
Upload handler for API Gateway.
Handles file uploads, stores them in S3, and triggers async Lambda processing.
"""

import json
import base64
import uuid
import boto3
import os
from typing import Dict, Any
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Environment variables (set by API Gateway/Lambda)
S3_BUCKET = os.environ.get('S3_BUCKET', 'room-detection-ai-blueprints-dev')
PROCESSING_LAMBDA_NAME = os.environ.get('PROCESSING_LAMBDA_NAME', 'room-detection-processor')


class UploadError(Exception):
    """Custom exception for upload errors."""
    pass


def generate_blueprint_id() -> str:
    """Generate a unique blueprint ID."""
    return f"bp_{uuid.uuid4().hex[:12]}"


def validate_file(file_content: bytes, content_type: str) -> None:
    """
    Validate uploaded file.
    
    Args:
        file_content: File content bytes
        content_type: MIME type of the file
        
    Raises:
        UploadError: If file is invalid
    """
    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB
    if len(file_content) > max_size:
        raise UploadError("file_too_large", f"File size exceeds 50MB limit. Size: {len(file_content)} bytes")
    
    # Check file type
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg']
    if content_type not in allowed_types:
        raise UploadError("invalid_file_format", f"File must be PNG or JPG format. Received: {content_type}")
    
    # Basic file signature validation
    if file_content[:4] != b'\x89PNG' and not file_content[:2] == b'\xff\xd8':
        raise UploadError("invalid_file_format", "File does not appear to be a valid PNG or JPG image")


def upload_to_s3(bucket: str, blueprint_id: str, file_content: bytes, content_type: str) -> str:
    """
    Upload file to S3.
    
    Args:
        bucket: S3 bucket name
        blueprint_id: Unique blueprint identifier
        file_content: File content bytes
        content_type: MIME type
        
    Returns:
        S3 key of uploaded file
    """
    # Determine file extension from content type
    extension = 'png' if content_type == 'image/png' else 'jpg'
    s3_key = f"uploads/{blueprint_id}/blueprint.{extension}"
    
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type,
            Metadata={
                'blueprint-id': blueprint_id
            }
        )
        return s3_key
    except ClientError as e:
        raise UploadError("s3_upload_failed", f"Failed to upload file to S3: {str(e)}")


def trigger_async_processing(blueprint_id: str, s3_bucket: str, s3_key: str) -> None:
    """
    Trigger async Lambda function to process the image.
    
    Args:
        blueprint_id: Unique blueprint identifier
        s3_bucket: S3 bucket name
        s3_key: S3 object key
    """
    payload = {
        'blueprint_id': blueprint_id,
        's3_bucket': s3_bucket,
        's3_key': s3_key
    }
    
    try:
        lambda_client.invoke(
            FunctionName=PROCESSING_LAMBDA_NAME,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
    except ClientError as e:
        raise UploadError("lambda_invocation_failed", f"Failed to trigger processing: {str(e)}")


def upload_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API Gateway handler for file upload endpoint.
    
    Expected event structure (API Gateway format):
    {
        "body": "<base64-encoded-multipart-form-data>",
        "headers": {
            "Content-Type": "multipart/form-data; boundary=..."
        },
        "isBase64Encoded": true
    }
    
    Returns:
        API Gateway response format
    """
    try:
        # Get environment variables
        bucket = event.get('S3_BUCKET', S3_BUCKET)
        lambda_name = event.get('PROCESSING_LAMBDA_NAME', PROCESSING_LAMBDA_NAME)
        
        # Parse multipart form data from API Gateway event
        # Note: API Gateway passes multipart data as base64-encoded body
        if event.get('isBase64Encoded'):
            body = base64.b64decode(event['body'])
        else:
            body = event['body'].encode('utf-8') if isinstance(event['body'], str) else event['body']
        
        # Extract file from multipart form data
        # This is a simplified parser - in production, use a proper multipart parser
        content_type = event.get('headers', {}).get('Content-Type', '')
        
        # For now, assume the file is passed directly in the body
        # In a real implementation, you'd parse multipart/form-data properly
        # This is a placeholder that needs proper multipart parsing
        
        # Generate blueprint ID
        blueprint_id = generate_blueprint_id()
        
        # Validate file (simplified - needs proper multipart parsing)
        # For now, we'll assume the body contains the raw image
        validate_file(body, content_type.split(';')[0].strip())
        
        # Upload to S3
        s3_key = upload_to_s3(bucket, blueprint_id, body, content_type.split(';')[0].strip())
        
        # Trigger async processing
        trigger_async_processing(blueprint_id, bucket, s3_key)
        
        # Return success response
        response_body = {
            'blueprint_id': blueprint_id,
            'status': 'processing',
            'message': 'Blueprint uploaded successfully. Processing started.'
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body)
        }
        
    except UploadError as e:
        error_code, error_message = e.args if len(e.args) >= 2 else (str(e), str(e))
        
        response_body = {
            'error': error_code,
            'message': error_message
        }
        
        status_code = 413 if error_code == 'file_too_large' else 400
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        response_body = {
            'error': 'internal_error',
            'message': f'An unexpected error occurred: {str(e)}'
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body)
        }

