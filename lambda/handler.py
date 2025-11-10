"""
Lambda function handler for room detection image processing.
Handles image preprocessing, SageMaker endpoint invocation, and response formatting.
Also handles API Gateway upload events with multipart form data parsing.
"""

import json
import os
import base64
import time
import uuid
import re
import boto3
from typing import Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError

# Lazy imports to avoid loading Pillow/NumPy for upload-only operations
_preprocess_image = None
_get_image_dimensions = None
_transform_coordinates_to_normalized = None
_status_manager = None

def get_status_manager():
    """Lazy load status_manager."""
    global _status_manager
    if _status_manager is None:
        from utils.status_manager import get_status_manager as _get_sm
        _status_manager = _get_sm()
    return _status_manager

def preprocess_image(*args, **kwargs):
    """Lazy load and call preprocess_image."""
    global _preprocess_image
    if _preprocess_image is None:
        from utils.image_processor import preprocess_image as _pi
        _preprocess_image = _pi
    return _preprocess_image(*args, **kwargs)

def get_image_dimensions(*args, **kwargs):
    """Lazy load and call get_image_dimensions."""
    global _get_image_dimensions
    if _get_image_dimensions is None:
        from utils.image_processor import get_image_dimensions as _gid
        _get_image_dimensions = _gid
    return _get_image_dimensions(*args, **kwargs)

def transform_coordinates_to_normalized(*args, **kwargs):
    """Lazy load and call transform_coordinates_to_normalized."""
    global _transform_coordinates_to_normalized
    if _transform_coordinates_to_normalized is None:
        from utils.coordinate_transformer import transform_coordinates_to_normalized as _tc
        _transform_coordinates_to_normalized = _tc
    return _transform_coordinates_to_normalized(*args, **kwargs)


# Initialize AWS clients
# AWS_REGION is automatically provided by Lambda runtime, use boto3's default session
sagemaker_runtime = boto3.client('sagemaker-runtime')
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Environment variables
SAGEMAKER_ENDPOINT_NAME = os.environ.get('SAGEMAKER_ENDPOINT_NAME', 'room-detection-yolov8-endpoint')
S3_BUCKET = os.environ.get('S3_BUCKET', 'room-detection-ai-blueprints-dev')
PROCESSING_LAMBDA_NAME = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'room-detection-ai-handler-dev')

# Initialize status manager
status_manager = get_status_manager()


class LambdaError(Exception):
    """Custom exception for Lambda function errors."""
    pass


def generate_blueprint_id() -> str:
    """Generate a unique blueprint ID."""
    return f"bp_{uuid.uuid4().hex[:12]}"


def parse_multipart_form_data(body: bytes, content_type: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Parse multipart form data to extract file content and content type.
    Simple, direct boundary-based parsing.
    
    Args:
        body: Raw body bytes
        content_type: Content-Type header value
        
    Returns:
        Tuple of (file_content, file_content_type) or (None, None) if parsing fails
    """
    try:
        # Extract boundary from content-type header
        boundary_match = re.search(r'boundary=([^;\s]+)', content_type)
        if not boundary_match:
            print(f"✗ No boundary found in Content-Type: {content_type}")
            return None, None
        
        boundary_str = boundary_match.group(1).strip('"\'')
        print(f"Boundary: {boundary_str}")
        
        # Find the file part in the body
        # Look for Content-Disposition with filename
        file_marker = b'Content-Disposition: form-data;'
        filename_marker = b'filename='
        
        # Find where the file part starts
        file_start = body.find(file_marker)
        if file_start == -1:
            print(f"✗ No Content-Disposition found in body")
            return None, None
        
        # Make sure this part has a filename (it's the file upload, not another form field)
        filename_pos = body.find(filename_marker, file_start)
        if filename_pos == -1:
            print(f"✗ No filename= found after Content-Disposition")
            return None, None
        
        print(f"✓ Found file part at position {file_start}")
        
        # Extract content type from this part (optional, default to image/png)
        file_content_type = 'image/png'
        ct_start = body.find(b'Content-Type:', file_start)
        if ct_start != -1 and ct_start < filename_pos + 200:  # Should be close to filename
            ct_end = body.find(b'\r\n', ct_start)
            if ct_end == -1:
                ct_end = body.find(b'\n', ct_start)
            if ct_end != -1:
                file_content_type = body[ct_start + 13:ct_end].decode('utf-8', errors='replace').strip()
                print(f"Content-Type: {file_content_type}")
        
        # Find the start of actual file data (after headers, marked by \r\n\r\n or \n\n)
        data_start = body.find(b'\r\n\r\n', file_start)
        if data_start != -1:
            data_start += 4  # Skip the \r\n\r\n
        else:
            data_start = body.find(b'\n\n', file_start)
            if data_start != -1:
                data_start += 2  # Skip the \n\n
            else:
                print(f"✗ Could not find end of headers (\\r\\n\\r\\n or \\n\\n)")
                return None, None
        
        print(f"File data starts at position {data_start}")
        
        # Find the end of file data (next boundary)
        # The closing boundary looks like: \r\n--boundary or \n--boundary
        boundary_bytes = b'--' + boundary_str.encode('ascii')
        
        # Find next boundary after the data start
        data_end = body.find(b'\r\n' + boundary_bytes, data_start)
        if data_end == -1:
            data_end = body.find(b'\n' + boundary_bytes, data_start)
        
        if data_end == -1:
            # Maybe there's no newline before the boundary?
            data_end = body.find(boundary_bytes, data_start)
            if data_end == -1:
                print(f"✗ Could not find closing boundary")
                return None, None
        
        # Extract the file content
        file_content = body[data_start:data_end]
        
        print(f"✓ Extracted {len(file_content)} bytes")
        print(f"  First 20 bytes (hex): {file_content[:20].hex() if len(file_content) >= 20 else file_content.hex()}")
        
        # Verify signature
        if len(file_content) >= 4:
            sig = file_content[:4].hex()
            if sig.startswith('89504e47'):
                print(f"  ✓ PNG signature detected")
            elif sig.startswith('ffd8'):
                print(f"  ✓ JPEG signature detected")
            else:
                print(f"  ⚠ Unexpected signature: {sig}")
        
        return file_content, file_content_type
        
    except Exception as e:
        print(f"✗ Error parsing multipart data: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def validate_file(file_content: bytes, content_type: str) -> Optional[str]:
    """
    Validate uploaded file.
    
    Args:
        file_content: File content bytes
        content_type: MIME type of the file
        
    Returns:
        Error message if invalid, None if valid
    """
    print(f"Validating file:")
    print(f"  Content-Type: {content_type}")
    print(f"  File size: {len(file_content)} bytes")
    
    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB
    if len(file_content) > max_size:
        return f"file_too_large: File size exceeds 50MB limit. Size: {len(file_content)} bytes"
    
    # Check file type
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg']
    if content_type not in allowed_types:
        return f"invalid_file_format: File must be PNG or JPG format. Received: {content_type}"
    
    # Basic file signature validation
    if len(file_content) < 4:
        return "invalid_file_format: File is too small to be a valid image"
    
    # Check signatures with detailed logging
    first_4_bytes = file_content[:4]
    first_4_hex = first_4_bytes.hex()
    print(f"  First 4 bytes (hex): {first_4_hex}")
    print(f"  First 4 bytes (repr): {repr(first_4_bytes)}")
    
    is_png = file_content[:4] == b'\x89PNG'
    is_jpeg = file_content[:2] == b'\xff\xd8'
    
    print(f"  PNG check: {is_png} (expected: 89504e47)")
    print(f"  JPEG check: {is_jpeg} (expected: ffd8xxxx)")
    
    if not (is_png or is_jpeg):
        # Try to identify what it actually is
        if first_4_hex.startswith('ffd8'):
            print("  ✓ Actually looks like JPEG based on hex")
            return None  # It's actually a JPEG
        elif first_4_hex.startswith('89504e47'):
            print("  ✓ Actually looks like PNG based on hex")
            return None  # It's actually a PNG
        else:
            return f"invalid_file_format: File does not appear to be a valid PNG or JPG image. Signature: {first_4_hex}"
    
    print("  ✓ File validation passed")
    return None


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
        raise LambdaError(f"Failed to upload file to S3: {str(e)}")


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
        
        # Parse response with error handling for encoding issues
        response_bytes = response['Body'].read()
        try:
            response_body = response_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1 if UTF-8 fails (shouldn't happen with JSON, but be safe)
            response_body = response_bytes.decode('latin-1', errors='replace')
        
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
        
        # TEMPORARY: Use mock data instead of SageMaker (for testing)
        # TODO: Re-enable SageMaker once endpoint is fixed
        # sagemaker_response = invoke_sagemaker_endpoint(preprocessed_bytes)
        # detected_rooms = sagemaker_response.get('detected_rooms', [])
        # processing_time_ms = sagemaker_response.get('processing_time_ms', 0)
        
        # Mock room detections for testing (using regular floats)
        detected_rooms = [
            {
                "id": "room_001",
                "bounding_box": [150, 100, 450, 350],
                "confidence": 0.92
            },
            {
                "id": "room_002", 
                "bounding_box": [500, 100, 800, 350],
                "confidence": 0.88
            },
            {
                "id": "room_003",
                "bounding_box": [150, 400, 350, 650],
                "confidence": 0.85
            },
            {
                "id": "room_004",
                "bounding_box": [400, 450, 600, 700],
                "confidence": 0.91
            }
        ]
        processing_time_ms = 150
        
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


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    from decimal import Decimal
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def add_cors_headers(headers: Dict[str, str] = None) -> Dict[str, str]:
    """Add CORS headers to response."""
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Content-Type': 'application/json'
    }
    if headers:
        cors_headers.update(headers)
    return cors_headers


def is_api_gateway_event(event: Dict[str, Any]) -> bool:
    """Check if event is from API Gateway."""
    return 'httpMethod' in event or 'requestContext' in event or 'path' in event


def handle_upload(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle API Gateway upload endpoint.
    
    Args:
        event: API Gateway event
        
    Returns:
        API Gateway response
    """
    try:
        # Parse body
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        
        print(f"Upload request received")
        print(f"  isBase64Encoded: {is_base64}")
        print(f"  body type: {type(body)}")
        print(f"  body length: {len(body) if isinstance(body, (str, bytes)) else 'N/A'}")
        
        # Get content type first (needed for debugging)
        headers = event.get('headers', {}) or {}
        content_type = headers.get('Content-Type') or headers.get('content-type', '')
        print(f"  Content-Type: {content_type}")
        
        # API Gateway passes multipart data - handle both base64 and raw string cases
        if is_base64:
            try:
                body_bytes = base64.b64decode(body)
                print(f"✓ Decoded base64 body: {len(body_bytes)} bytes")
            except Exception as e:
                print(f"✗ Failed to decode base64: {e}")
                return {
                    'statusCode': 400,
                    'headers': add_cors_headers(),
                    'body': json.dumps({
                        'error': 'invalid_request',
                        'message': f'Failed to decode base64 body: {str(e)}'
                    })
                }
        elif isinstance(body, str):
            # Try base64 decode first (API Gateway might not set isBase64Encoded correctly)
            try:
                decoded = base64.b64decode(body, validate=True)
                # Check if decoded data looks like multipart or image
                if b'Content-Disposition' in decoded or b'boundary' in decoded.lower():
                    body_bytes = decoded
                    print(f"✓ Detected base64-encoded multipart data: {len(body_bytes)} bytes")
                elif len(decoded) > 4 and (decoded[:4] == b'\x89PNG' or decoded[:2] == b'\xff\xd8'):
                    body_bytes = decoded
                    print(f"✓ Detected base64-encoded image: {len(body_bytes)} bytes")
                else:
                    # Not base64, encode as bytes using latin-1 to preserve byte values
                    body_bytes = body.encode('latin-1', errors='replace')
                    print(f"Using latin-1 encoding for body string: {len(body_bytes)} bytes")
            except Exception as decode_err:
                # Not base64, encode as bytes using latin-1 to preserve all byte values
                # latin-1 is a 1:1 mapping that won't corrupt binary data like UTF-8 does
                print(f"Base64 decode failed ({decode_err}), using latin-1 encoding")
                body_bytes = body.encode('latin-1', errors='replace')
                print(f"Using latin-1 encoding (not base64): {len(body_bytes)} bytes")
        else:
            body_bytes = body
            print(f"Body is already bytes: {len(body_bytes)} bytes")
        
        # Validate we have data
        if not body_bytes or len(body_bytes) == 0:
            return {
                'statusCode': 400,
                'headers': add_cors_headers(),
                'body': json.dumps({
                    'error': 'invalid_request',
                    'message': 'Request body is empty'
                })
            }
        
        # Debug: Show first 200 bytes of body
        preview = body_bytes[:200] if len(body_bytes) > 200 else body_bytes
        print(f"Body preview (first {len(preview)} bytes):")
        print(f"  Hex: {preview.hex()[:100]}...")
        print(f"  Text (safe): {preview[:100].decode('utf-8', errors='replace')}")
        
        # Check if content type indicates multipart
        if not content_type or 'multipart' not in content_type.lower():
            return {
                'statusCode': 400,
                'headers': add_cors_headers(),
                'body': json.dumps({
                    'error': 'invalid_request',
                    'message': f'Expected multipart/form-data, got: {content_type}'
                })
            }
        
        # Parse multipart form data
        print("Parsing multipart form data...")
        file_content, file_content_type = parse_multipart_form_data(body_bytes, content_type)
        
        if not file_content:
            print("✗ Failed to extract file from multipart data")
            # Return helpful error message
            return {
                'statusCode': 400,
                'headers': add_cors_headers(),
                'body': json.dumps({
                    'error': 'invalid_request',
                    'message': 'No file found in multipart request. Please ensure you are sending a file with the field name "file".'
                })
            }
        
        # Validate file
        validation_error = validate_file(file_content, file_content_type)
        if validation_error:
            error_code, error_message = validation_error.split(':', 1)
            status_code = 413 if error_code.strip() == 'file_too_large' else 400
            return {
                'statusCode': status_code,
                'headers': add_cors_headers(),
                'body': json.dumps({
                    'error': error_code.strip(),
                    'message': error_message.strip()
                })
            }
        
        # Generate blueprint ID
        blueprint_id = generate_blueprint_id()
        
        # Upload to S3
        s3_key = upload_to_s3(S3_BUCKET, blueprint_id, file_content, file_content_type)
        
        # Create initial status entry
        try:
            status_manager.create_status(
                blueprint_id=blueprint_id,
                status='processing',
                message='Blueprint uploaded successfully. Processing started.'
            )
        except:
            pass  # Continue even if status creation fails
        
        # Trigger async processing by invoking this same Lambda function
        processing_payload = {
            'blueprint_id': blueprint_id,
            's3_bucket': S3_BUCKET,
            's3_key': s3_key
        }
        
        try:
            lambda_client.invoke(
                FunctionName=PROCESSING_LAMBDA_NAME,
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(processing_payload)
            )
        except Exception as e:
            print(f"Warning: Failed to trigger async processing: {e}")
            # Don't fail the upload if async trigger fails
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': add_cors_headers(),
            'body': json.dumps({
                'blueprint_id': blueprint_id,
                'status': 'processing',
                'message': 'Blueprint uploaded successfully. Processing started.'
            })
        }
        
    except Exception as e:
        print(f"Upload error: {e}")
        return {
            'statusCode': 500,
            'headers': add_cors_headers(),
            'body': json.dumps({
                'error': 'internal_error',
                'message': f'An unexpected error occurred: {str(e)}'
            })
        }


def handle_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle API Gateway status endpoint.
    
    Args:
        event: API Gateway event
        
    Returns:
        API Gateway response
    """
    try:
        # Extract blueprint_id from path parameters
        path_params = event.get('pathParameters', {}) or {}
        blueprint_id = path_params.get('blueprint_id')
        
        if not blueprint_id:
            return {
                'statusCode': 400,
                'headers': add_cors_headers(),
                'body': json.dumps({
                    'error': 'missing_blueprint_id',
                    'message': 'blueprint_id is required in path'
                })
            }
        
        # Get status from DynamoDB
        status_data = status_manager.get_status(blueprint_id)
        
        if not status_data:
            return {
                'statusCode': 404,
                'headers': add_cors_headers(),
                'body': json.dumps({
                    'error': 'blueprint_not_found',
                    'message': f'Blueprint with ID {blueprint_id} not found',
                    'blueprint_id': blueprint_id
                })
            }
        
        # Format response based on status
        status = status_data.get('status', 'unknown')
        
        if status == 'completed':
            response_body = {
                'blueprint_id': blueprint_id,
                'status': 'completed',
                'processing_time_ms': status_data.get('processing_time_ms', 0),
                'detected_rooms': status_data.get('detected_rooms', [])
            }
        elif status == 'failed':
            response_body = {
                'blueprint_id': blueprint_id,
                'status': 'failed',
                'error': status_data.get('error', 'processing_failed'),
                'message': status_data.get('message', 'Processing failed')
            }
        else:  # processing
            response_body = {
                'blueprint_id': blueprint_id,
                'status': 'processing',
                'message': status_data.get('message', 'Analyzing blueprint...')
            }
        
        return {
            'statusCode': 200,
            'headers': add_cors_headers(),
            'body': json.dumps(response_body, default=decimal_to_float)
        }
        
    except Exception as e:
        print(f"Status error: {e}")
        return {
            'statusCode': 500,
            'headers': add_cors_headers(),
            'body': json.dumps({
                'error': 'internal_error',
                'message': f'An unexpected error occurred: {str(e)}'
            })
        }


def handle_processing(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle direct Lambda invocation for image processing.
    
    Args:
        event: Direct invocation event with blueprint_id, s3_bucket, s3_key
        
    Returns:
        Processing result
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
                'headers': add_cors_headers(),
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
                'headers': add_cors_headers(),
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
            'headers': add_cors_headers(),
            'body': json.dumps(result, default=decimal_to_float)
        }
        
    except LambdaError as e:
        # Return error response
        blueprint_id = event.get('blueprint_id', 'unknown')
        return {
            'statusCode': 500,
            'headers': add_cors_headers(),
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
            'headers': add_cors_headers(),
            'body': json.dumps({
                'blueprint_id': blueprint_id,
                'status': 'failed',
                'error': 'internal_error',
                'message': f'An unexpected error occurred: {str(e)}'
            })
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    Handles both:
    1. API Gateway upload events (POST /api/v1/blueprints/upload)
    2. API Gateway status events (GET /api/v1/blueprints/{id}/status)
    3. Direct Lambda invocation for processing:
       {
           "blueprint_id": "bp_abc123",
           "s3_bucket": "room-detection-ai-blueprints-dev",
           "s3_key": "uploads/bp_abc123/image.png"
       }
    
    Returns:
        API response dictionary
    """
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': add_cors_headers(),
            'body': ''
        }
    
    # Check if this is an API Gateway event
    if is_api_gateway_event(event):
        # Route based on HTTP method and path
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        # Handle upload endpoint: POST /api/v1/blueprints/upload
        if http_method == 'POST' and '/upload' in path:
            return handle_upload(event)
        
        # Handle status endpoint: GET /api/v1/blueprints/{blueprint_id}/status
        if http_method == 'GET' and '/status' in path:
            return handle_status(event)
        
        # Unknown API Gateway route
        return {
            'statusCode': 404,
            'headers': add_cors_headers(),
            'body': json.dumps({
                'error': 'not_found',
                'message': f'No handler for {http_method} {path}'
            })
        }
    
    # Direct invocation for image processing
    return handle_processing(event)

