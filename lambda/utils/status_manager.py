"""
Status manager for tracking blueprint processing status in DynamoDB.
"""

import os
import time
import json
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Table name from environment variable or default
STATUS_TABLE_NAME = os.environ.get('STATUS_TABLE_NAME', 'room-detection-status-dev')

# TTL for status records (7 days)
STATUS_TTL_SECONDS = 7 * 24 * 60 * 60


class StatusManagerError(Exception):
    """Custom exception for status manager errors."""
    pass


class StatusManager:
    """Manages blueprint processing status in DynamoDB."""
    
    def __init__(self, table_name: str = None):
        """
        Initialize status manager.
        
        Args:
            table_name: DynamoDB table name (defaults to STATUS_TABLE_NAME env var)
        """
        self.table_name = table_name or STATUS_TABLE_NAME
        self.table = dynamodb.Table(self.table_name)
    
    def create_status(self, blueprint_id: str, message: str = "Processing started") -> None:
        """
        Create initial status record.
        
        Args:
            blueprint_id: Unique blueprint identifier
            message: Status message
        """
        try:
            ttl = int(time.time()) + STATUS_TTL_SECONDS
            
            self.table.put_item(
                Item={
                    'blueprint_id': blueprint_id,
                    'status': 'processing',
                    'message': message,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'ttl': ttl
                }
            )
        except ClientError as e:
            raise StatusManagerError(f"Failed to create status: {str(e)}")
    
    def update_status(
        self,
        blueprint_id: str,
        status: str,
        message: str = None,
        processing_time_ms: int = None,
        detected_rooms: list = None,
        error: str = None
    ) -> None:
        """
        Update status record.
        
        Args:
            blueprint_id: Unique blueprint identifier
            status: Status value ('processing', 'completed', 'failed')
            message: Optional status message
            processing_time_ms: Optional processing time in milliseconds
            detected_rooms: Optional list of detected rooms
            error: Optional error code
        """
        try:
            update_expression_parts = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            # Base updates
            update_expression_parts.append("#status = :status")
            expression_attribute_names['#status'] = 'status'
            expression_attribute_values[':status'] = status
            
            update_expression_parts.append("#updated_at = :updated_at")
            expression_attribute_names['#updated_at'] = 'updated_at'
            expression_attribute_values[':updated_at'] = datetime.utcnow().isoformat()
            
            # Optional fields
            if message is not None:
                update_expression_parts.append("#message = :message")
                expression_attribute_names['#message'] = 'message'
                expression_attribute_values[':message'] = message
            
            if processing_time_ms is not None:
                update_expression_parts.append("processing_time_ms = :processing_time_ms")
                expression_attribute_values[':processing_time_ms'] = processing_time_ms
            
            if detected_rooms is not None:
                # Convert floats to Decimal for DynamoDB
                detected_rooms_converted = json.loads(json.dumps(detected_rooms), parse_float=Decimal)
                update_expression_parts.append("detected_rooms = :detected_rooms")
                expression_attribute_values[':detected_rooms'] = detected_rooms_converted
            
            if error is not None:
                update_expression_parts.append("#error = :error")
                expression_attribute_names['#error'] = 'error'
                expression_attribute_values[':error'] = error
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            self.table.update_item(
                Key={'blueprint_id': blueprint_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None,
                ExpressionAttributeValues=expression_attribute_values
            )
        except ClientError as e:
            raise StatusManagerError(f"Failed to update status: {str(e)}")
    
    def get_status(self, blueprint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status record.
        
        Args:
            blueprint_id: Unique blueprint identifier
            
        Returns:
            Status dictionary or None if not found (all Decimals converted to floats)
        """
        try:
            response = self.table.get_item(
                Key={'blueprint_id': blueprint_id}
            )
            
            if 'Item' in response:
                item = response['Item']
                # Remove TTL from response (internal field)
                item.pop('ttl', None)
                
                # Convert ALL Decimals to floats recursively
                item = self._convert_decimals_to_floats(item)
                
                return item
            return None
        except ClientError as e:
            raise StatusManagerError(f"Failed to get status: {str(e)}")
    
    @staticmethod
    def _decimal_default(obj):
        """Helper to convert Decimal to float for JSON serialization."""
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError
    
    @staticmethod
    def _convert_decimals_to_floats(obj):
        """Recursively convert all Decimal objects to floats."""
        if isinstance(obj, list):
            return [StatusManager._convert_decimals_to_floats(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: StatusManager._convert_decimals_to_floats(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj
    
    def mark_completed(
        self,
        blueprint_id: str,
        processing_time_ms: int,
        detected_rooms: list,
        message: str = "Processing completed successfully"
    ) -> None:
        """
        Mark status as completed.
        
        Args:
            blueprint_id: Unique blueprint identifier
            processing_time_ms: Processing time in milliseconds
            detected_rooms: List of detected rooms
            message: Optional completion message
        """
        self.update_status(
            blueprint_id=blueprint_id,
            status='completed',
            message=message,
            processing_time_ms=processing_time_ms,
            detected_rooms=detected_rooms
        )
    
    def mark_failed(
        self,
        blueprint_id: str,
        error: str,
        message: str = None
    ) -> None:
        """
        Mark status as failed.
        
        Args:
            blueprint_id: Unique blueprint identifier
            error: Error code
            message: Optional error message
        """
        self.update_status(
            blueprint_id=blueprint_id,
            status='failed',
            error=error,
            message=message or f"Processing failed: {error}"
        )


# Singleton instance
_status_manager = None


def get_status_manager() -> StatusManager:
    """Get singleton status manager instance."""
    global _status_manager
    if _status_manager is None:
        _status_manager = StatusManager()
    return _status_manager

