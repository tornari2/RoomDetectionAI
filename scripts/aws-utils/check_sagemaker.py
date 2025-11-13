#!/usr/bin/env python3
"""
Check SageMaker endpoint status
"""

import boto3

client = boto3.client('sagemaker', region_name='us-east-2')

endpoint_name = 'room-detection-yolov8-endpoint'

print(f"Checking endpoint: {endpoint_name}")
print("=" * 60)

try:
    response = client.describe_endpoint(EndpointName=endpoint_name)
    
    print(f"Endpoint Name: {response['EndpointName']}")
    print(f"Status: {response['EndpointStatus']}")
    print(f"Created: {response['CreationTime']}")
    print(f"Last Modified: {response['LastModifiedTime']}")
    
    if response['EndpointStatus'] != 'InService':
        print("\n⚠️  ENDPOINT IS NOT RUNNING!")
        print(f"Current status: {response['EndpointStatus']}")
        
        if 'FailureReason' in response:
            print(f"Failure reason: {response['FailureReason']}")
    else:
        print("\n✅ Endpoint is InService (running)")
        print("\nEndpoint Config:")
        config = client.describe_endpoint_config(
            EndpointConfigName=response['EndpointConfigName']
        )
        print(f"Instance Type: {config['ProductionVariants'][0]['InstanceType']}")
        print(f"Initial Instance Count: {config['ProductionVariants'][0]['InitialInstanceCount']}")
        
except client.exceptions.ClientError as e:
    if e.response['Error']['Code'] == 'ValidationException':
        print(f"\n❌ ENDPOINT DOES NOT EXIST!")
        print(f"Endpoint '{endpoint_name}' was not found.")
    else:
        print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 60)

