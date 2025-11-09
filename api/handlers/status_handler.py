"""
Status handler for API Gateway.
Handles status polling requests for blueprint processing status.
"""

import json
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Table name for status storage (will be created by CloudFormation)
STATUS_TABLE_NAME = 'room-detection-status'


class StatusError(Exception):
    """Custom exception for status errors."""
    pass


def get_status(blueprint_id: str) -> Optional[Dict[str, Any]]:
    """
    Get processing status from DynamoDB.
    
    Args:
        blueprint_id: Unique blueprint identifier
        
    Returns:
        Status dictionary or None if not found
    """
    try:
        table = dynamodb.Table(STATUS_TABLE_NAME)
        response = table.get_item(
            Key={'blueprint_id': blueprint_id}
        )
        
        if 'Item' in response:
            return response['Item']
        return None
        
    except ClientError as e:
        raise StatusError(f"Failed to retrieve status: {str(e)}")


def status_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API Gateway handler for status polling endpoint.
    
    Expected event structure:
    {
        "pathParameters": {
            "blueprint_id": "bp_abc123"
        }
    }
    
    Returns:
        API Gateway response format
    """
    try:
        # Extract blueprint_id from path parameters
        path_params = event.get('pathParameters', {}) or {}
        blueprint_id = path_params.get('blueprint_id')
        
        if not blueprint_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'missing_blueprint_id',
                    'message': 'blueprint_id is required in path'
                })
            }
        
        # Get status from DynamoDB
        status_data = get_status(blueprint_id)
        
        if not status_data:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
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
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body)
        }
        
    except StatusError as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'status_retrieval_failed',
                'message': str(e)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'internal_error',
                'message': f'An unexpected error occurred: {str(e)}'
            })
        }

