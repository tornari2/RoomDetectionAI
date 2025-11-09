#!/usr/bin/env python3
"""
Test inference on SageMaker Serverless Inference endpoint.
"""

import argparse
import json
import base64
import time
import boto3
from pathlib import Path
from PIL import Image
import io


def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')


def test_inference(endpoint_name, image_path, region='us-east-2', use_base64=True):
    """Test inference on SageMaker endpoint."""
    runtime_client = boto3.client('sagemaker-runtime', region_name=region)
    
    print("=" * 80)
    print("Testing SageMaker Inference Endpoint")
    print("=" * 80)
    print(f"Endpoint: {endpoint_name}")
    print(f"Image: {image_path}")
    print(f"Region: {region}")
    print("=" * 80)
    print()
    
    # Prepare payload
    if use_base64:
        # Encode image as base64 JSON
        image_b64 = encode_image(image_path)
        payload = json.dumps({
            "image": image_b64
        })
        content_type = 'application/json'
    else:
        # Send raw image bytes
        with open(image_path, 'rb') as f:
            payload = f.read()
        content_type = 'image/png' if image_path.endswith('.png') else 'image/jpeg'
    
    print(f"Sending request...")
    print(f"  Content type: {content_type}")
    print(f"  Payload size: {len(payload)} bytes")
    print()
    
    # Invoke endpoint
    start_time = time.time()
    try:
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType=content_type,
            Body=payload
        )
        
        # Read response
        response_body = response['Body'].read()
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Parse response
        result = json.loads(response_body)
        
        print("✅ Inference successful!")
        print()
        print("Response:")
        print("-" * 80)
        print(json.dumps(result, indent=2))
        print("-" * 80)
        print()
        print(f"Total time: {elapsed_time:.2f}ms")
        print(f"Processing time: {result.get('processing_time_ms', 'N/A')}ms")
        print(f"Detected rooms: {len(result.get('detected_rooms', []))}")
        
        # Validate response format
        print()
        print("Response Format Validation:")
        print("-" * 80)
        required_fields = ['status', 'detected_rooms', 'processing_time_ms']
        all_valid = True
        
        for field in required_fields:
            if field in result:
                print(f"  ✅ {field}: Present")
            else:
                print(f"  ❌ {field}: Missing")
                all_valid = False
        
        if result.get('status') == 'success':
            print(f"  ✅ Status: success")
        else:
            print(f"  ⚠️  Status: {result.get('status')}")
            all_valid = False
        
        # Validate detected_rooms format
        rooms = result.get('detected_rooms', [])
        if rooms:
            first_room = rooms[0]
            room_fields = ['id', 'bounding_box', 'confidence']
            for field in room_fields:
                if field in first_room:
                    print(f"  ✅ Room.{field}: Present")
                else:
                    print(f"  ❌ Room.{field}: Missing")
                    all_valid = False
            
            # Validate bounding_box format
            bbox = first_room.get('bounding_box', [])
            if len(bbox) == 4:
                print(f"  ✅ bounding_box: Valid format [x_min, y_min, x_max, y_max]")
                if all(0 <= val <= 1000 for val in bbox):
                    print(f"  ✅ bounding_box: Values in 0-1000 range")
                else:
                    print(f"  ⚠️  bounding_box: Some values outside 0-1000 range")
            else:
                print(f"  ❌ bounding_box: Invalid format (expected 4 values)")
                all_valid = False
        
        print()
        if all_valid:
            print("✅ Response format matches API specification!")
        else:
            print("⚠️  Response format has some issues")
        
        return result
        
    except Exception as e:
        print(f"❌ Error invoking endpoint: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='Test SageMaker inference endpoint')
    parser.add_argument(
        '--endpoint-name',
        type=str,
        required=True,
        help='SageMaker endpoint name'
    )
    parser.add_argument(
        '--image',
        type=str,
        required=True,
        help='Path to test image (PNG or JPG)'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-2',
        help='AWS region (default: us-east-2)'
    )
    parser.add_argument(
        '--raw',
        action='store_true',
        help='Send raw image bytes instead of base64 JSON'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save response JSON to file'
    )
    
    args = parser.parse_args()
    
    # Validate image exists
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    # Test inference
    result = test_inference(
        args.endpoint_name,
        str(image_path),
        args.region,
        use_base64=not args.raw
    )
    
    # Save output if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Response saved to: {args.output}")


if __name__ == '__main__':
    main()

