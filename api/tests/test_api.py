"""
API tests for upload and status endpoints.
"""

import json
import base64
import pytest
from unittest.mock import Mock, patch, MagicMock
from api.handlers.upload_handler import upload_handler, generate_blueprint_id, validate_file
from api.handlers.status_handler import status_handler, get_status


class TestUploadHandler:
    """Tests for upload handler."""
    
    def test_generate_blueprint_id(self):
        """Test blueprint ID generation."""
        blueprint_id = generate_blueprint_id()
        assert blueprint_id.startswith('bp_')
        assert len(blueprint_id) > 3
    
    def test_validate_file_valid_png(self):
        """Test file validation with valid PNG."""
        # PNG file signature
        png_content = b'\x89PNG\r\n\x1a\n' + b'0' * 1000
        validate_file(png_content, 'image/png')
    
    def test_validate_file_valid_jpg(self):
        """Test file validation with valid JPG."""
        # JPG file signature
        jpg_content = b'\xff\xd8\xff\xe0' + b'0' * 1000
        validate_file(jpg_content, 'image/jpeg')
    
    def test_validate_file_too_large(self):
        """Test file validation with file exceeding size limit."""
        large_content = b'0' * (51 * 1024 * 1024)  # 51MB
        with pytest.raises(Exception) as exc_info:
            validate_file(large_content, 'image/png')
        assert 'file_too_large' in str(exc_info.value) or 'exceeds' in str(exc_info.value).lower()
    
    def test_validate_file_invalid_format(self):
        """Test file validation with invalid format."""
        invalid_content = b'not an image'
        with pytest.raises(Exception) as exc_info:
            validate_file(invalid_content, 'application/pdf')
        assert 'invalid_file_format' in str(exc_info.value) or 'PNG or JPG' in str(exc_info.value)
    
    @patch('api.handlers.upload_handler.s3_client')
    @patch('api.handlers.upload_handler.lambda_client')
    def test_upload_handler_success(self, mock_lambda, mock_s3):
        """Test successful upload handler."""
        # Mock S3 upload
        mock_s3.put_object.return_value = {}
        
        # Mock Lambda invocation
        mock_lambda.invoke.return_value = {'StatusCode': 202}
        
        # Create test event
        png_content = b'\x89PNG\r\n\x1a\n' + b'0' * 1000
        encoded_body = base64.b64encode(png_content).decode('utf-8')
        
        event = {
            'body': encoded_body,
            'isBase64Encoded': True,
            'headers': {
                'Content-Type': 'image/png'
            },
            'S3_BUCKET': 'test-bucket'
        }
        
        response = upload_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'blueprint_id' in body
        assert body['status'] == 'processing'
        assert body['message'] == 'Blueprint uploaded successfully. Processing started.'
    
    def test_upload_handler_invalid_file(self):
        """Test upload handler with invalid file."""
        event = {
            'body': base64.b64encode(b'invalid').decode('utf-8'),
            'isBase64Encoded': True,
            'headers': {
                'Content-Type': 'application/pdf'
            }
        }
        
        response = upload_handler(event, None)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body


class TestStatusHandler:
    """Tests for status handler."""
    
    @patch('api.handlers.status_handler.dynamodb')
    def test_status_handler_processing(self, mock_dynamodb):
        """Test status handler with processing status."""
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'blueprint_id': 'bp_test123',
                'status': 'processing',
                'message': 'Analyzing blueprint...'
            }
        }
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'pathParameters': {
                'blueprint_id': 'bp_test123'
            }
        }
        
        response = status_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['blueprint_id'] == 'bp_test123'
        assert body['status'] == 'processing'
    
    @patch('api.handlers.status_handler.dynamodb')
    def test_status_handler_completed(self, mock_dynamodb):
        """Test status handler with completed status."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'blueprint_id': 'bp_test123',
                'status': 'completed',
                'processing_time_ms': 15420,
                'detected_rooms': [
                    {
                        'id': 'room_001',
                        'bounding_box': [50, 50, 200, 300],
                        'confidence': 0.95
                    }
                ]
            }
        }
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'pathParameters': {
                'blueprint_id': 'bp_test123'
            }
        }
        
        response = status_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'completed'
        assert 'detected_rooms' in body
        assert 'processing_time_ms' in body
    
    @patch('api.handlers.status_handler.dynamodb')
    def test_status_handler_not_found(self, mock_dynamodb):
        """Test status handler with non-existent blueprint."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_dynamodb.Table.return_value = mock_table
        
        event = {
            'pathParameters': {
                'blueprint_id': 'bp_nonexistent'
            }
        }
        
        response = status_handler(event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'blueprint_not_found'
    
    def test_status_handler_missing_id(self):
        """Test status handler with missing blueprint_id."""
        event = {
            'pathParameters': {}
        }
        
        response = status_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

