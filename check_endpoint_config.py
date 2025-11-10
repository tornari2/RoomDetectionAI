#!/usr/bin/env python3
"""
Check SageMaker endpoint configuration details
"""

import boto3

sm = boto3.client('sagemaker', region_name='us-east-2')

endpoint_name = 'room-detection-yolov8-endpoint'

# Get endpoint
endpoint = sm.describe_endpoint(EndpointName=endpoint_name)
config_name = endpoint['EndpointConfigName']

# Get endpoint config
config = sm.describe_endpoint_config(EndpointConfigName=config_name)

print("SageMaker Endpoint Configuration:")
print("=" * 60)

for variant in config['ProductionVariants']:
    print(f"Variant Name: {variant['VariantName']}")
    print(f"Instance Type: {variant.get('InstanceType', variant.get('ServerlessConfig', {}).get('MemorySizeInMB', 'Unknown'))}")
    print(f"Initial Instance Count: {variant.get('InitialInstanceCount', 'N/A')}")
    print(f"Model Name: {variant['ModelName']}")
    
    if 'ServerlessConfig' in variant:
        print("\n🔍 SERVERLESS ENDPOINT DETECTED:")
        print(f"  Memory: {variant['ServerlessConfig']['MemorySizeInMB']} MB")
        print(f"  Max Concurrency: {variant['ServerlessConfig']['MaxConcurrency']}")
        print("\n⚠️  Serverless endpoints can be unstable for YOLOv8!")
        print("   Recommendation: Use ml.t2.medium or ml.m5.large instead")

print("\n" + "=" * 60)

