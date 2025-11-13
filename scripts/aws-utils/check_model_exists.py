#!/usr/bin/env python3
"""
Check if model exists in SageMaker
"""

import boto3

sm = boto3.client('sagemaker', region_name='us-east-2')

endpoint_name = 'room-detection-yolov8-endpoint'

# Get endpoint
endpoint = sm.describe_endpoint(EndpointName=endpoint_name)
config_name = endpoint['EndpointConfigName']

# Get endpoint config
config = sm.describe_endpoint_config(EndpointConfigName=config_name)
model_name = config['ProductionVariants'][0]['ModelName']

# Get model
model = sm.describe_model(ModelName=model_name)

print(f"Model Name: {model['ModelName']}")
print(f"Model Data URL: {model['PrimaryContainer']['ModelDataUrl']}")
print(f"Image: {model['PrimaryContainer']['Image']}")

# Check if model file exists in S3
s3 = boto3.client('s3', region_name='us-east-2')
model_s3_url = model['PrimaryContainer']['ModelDataUrl']

if model_s3_url.startswith('s3://'):
    # Parse S3 URL
    parts = model_s3_url.replace('s3://', '').split('/', 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ''
    
    print(f"\nChecking S3: s3://{bucket}/{key}")
    
    try:
        obj = s3.head_object(Bucket=bucket, Key=key)
        size_mb = obj['ContentLength'] / (1024 * 1024)
        print(f"✅ Model file exists: {size_mb:.2f} MB")
        print(f"Last Modified: {obj['LastModified']}")
    except:
        print(f"❌ MODEL FILE MISSING IN S3!")
        print("The endpoint is broken - model file doesn't exist")

