"""
Unit tests for Lambda function handler.
"""

import json
import base64
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

from handler import lambda_handler, process_image, invoke_sagemaker_endpoint, download_image_from_s3
from utils.image_processor import resize_image, normalize_image, preprocess_image, get_image_dimensions
from utils.coordinate_transformer import transform_coordinates_to_normalized, transform_bounding_box


def create_test_image(width=800, height=600):
    """Create a test image."""
    image = Image.new('RGB', (width, height), color='white')
    return image


def image_to_bytes(image):
    """Convert PIL Image to bytes."""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


class TestImageProcessor:
    """Test image preprocessing functions."""
    
    def test_resize_image(self):
        """Test image resizing."""
        image = create_test_image(800, 600)
        resized = resize_image(image, (640, 640))
        
        assert resized.size == (640, 640)
        assert isinstance(resized, Image.Image)
    
    def test_normalize_image(self):
        """Test image normalization."""
        image = create_test_image(100, 100)
        normalized = normalize_image(image)
        
        assert normalized.max() <= 1.0
        assert normalized.min() >= 0.0
        assert normalized.shape == (100, 100, 3)
    
    def test_preprocess_image(self):
        """Test complete preprocessing pipeline."""
        image = create_test_image(800, 600)
        image_bytes = image_to_bytes(image)
        
        preprocessed = preprocess_image(image_bytes, (640, 640))
        
        assert preprocessed.size == (640, 640)
        assert isinstance(preprocessed, Image.Image)
    
    def test_get_image_dimensions(self):
        """Test getting image dimensions."""
        image = create_test_image(800, 600)
        image_bytes = image_to_bytes(image)
        
        width, height = get_image_dimensions(image_bytes)
        
        assert width == 800
        assert height == 600


class TestCoordinateTransformer:
    """Test coordinate transformation functions."""
    
    def test_transform_coordinates_to_normalized(self):
        """Test coordinate transformation to 0-1000 range."""
        x_min, y_min, x_max, y_max = transform_coordinates_to_normalized(
            100, 50, 300, 250,
            800, 600
        )
        
        assert 0 <= x_min <= 1000
        assert 0 <= y_min <= 1000
        assert 0 <= x_max <= 1000
        assert 0 <= y_max <= 1000
        assert x_min < x_max
        assert y_min < y_max
    
    def test_transform_bounding_box(self):
        """Test bounding box transformation."""
        bounding_box = [50, 50, 200, 200]
        transformed = transform_bounding_box(
            bounding_box,
            original_width=800,
            original_height=600,
            resized_width=640,
            resized_height=640
        )
        
        assert len(transformed) == 4
        assert all(0 <= coord <= 1000 for coord in transformed)


class TestLambdaHandler:
    """Test Lambda handler function."""
    
    @patch('handler.s3_client')
    @patch('handler.sagemaker_runtime')
    def test_lambda_handler_success(self, mock_sagemaker, mock_s3):
        """Test successful Lambda invocation."""
        # Setup mocks
        test_image = create_test_image(800, 600)
        image_bytes = image_to_bytes(test_image)
        
        mock_s3.get_object.return_value = {'Body': Mock(read=lambda: image_bytes)}
        
        mock_sagemaker_response = Mock()
        mock_sagemaker_response.read.return_value.decode.return_value = json.dumps({
            'status': 'success',
            'processing_time_ms': 1500,
            'detected_rooms': [
                {
                    'id': 'room_001',
                    'bounding_box': [100, 100, 200, 200],
                    'confidence': 0.95
                }
            ]
        })
        mock_sagemaker.invoke_endpoint.return_value = {'Body': mock_sagemaker_response}
        
        # Test event
        event = {
            'blueprint_id': 'bp_test123',
            's3_bucket': 'test-bucket',
            's3_key': 'test/image.png'
        }
        
        # Invoke handler
        response = lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'completed'
        assert body['blueprint_id'] == 'bp_test123'
        assert 'detected_rooms' in body
    
    def test_lambda_handler_missing_blueprint_id(self):
        """Test Lambda handler with missing blueprint_id."""
        event = {
            's3_bucket': 'test-bucket',
            's3_key': 'test/image.png'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'failed'
        assert 'missing_blueprint_id' in body['error']
    
    def test_lambda_handler_missing_s3_key(self):
        """Test Lambda handler with missing s3_key."""
        event = {
            'blueprint_id': 'bp_test123',
            's3_bucket': 'test-bucket'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'failed'
        assert 'missing_s3_key' in body['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

