#!/usr/bin/env python3
"""
Fix SageMaker endpoint - switch from Serverless to ml.t2.medium
"""

import boto3
import time

sm = boto3.client('sagemaker', region_name='us-east-2')

endpoint_name = 'room-detection-yolov8-endpoint'
model_name = 'room-detection-yolov8-model'
new_config_name = f'room-detection-yolov8-config-realtime-{int(time.time())}'

print("Creating new endpoint configuration with ml.t2.medium...")
print("=" * 60)

# Create new endpoint config with real instance
try:
    config_response = sm.create_endpoint_config(
        EndpointConfigName=new_config_name,
        ProductionVariants=[
            {
                'VariantName': 'AllTraffic',
                'ModelName': model_name,
                'InstanceType': 'ml.t2.medium',  # Real instance, not serverless
                'InitialInstanceCount': 1,
                'InitialVariantWeight': 1.0
            }
        ]
    )
    
    print(f"✅ Created new config: {new_config_name}")
    print(f"   Instance Type: ml.t2.medium")
    print(f"   Cost: ~$0.065/hour while running")
    
except Exception as e:
    print(f"❌ Failed to create config: {e}")
    exit(1)

# Update endpoint to use new config
print("\nUpdating endpoint...")
print("⏳ This takes 5-10 minutes...")

try:
    update_response = sm.update_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=new_config_name
    )
    
    print(f"✅ Update initiated!")
    print(f"   Endpoint: {endpoint_name}")
    print(f"   Status: Updating...")
    
    # Wait for update to complete
    print("\nWaiting for endpoint to be InService...")
    
    while True:
        status = sm.describe_endpoint(EndpointName=endpoint_name)
        current_status = status['EndpointStatus']
        
        print(f"   Status: {current_status}...", end='\r')
        
        if current_status == 'InService':
            print("\n\n🎉 SUCCESS! Endpoint is now running on ml.t2.medium")
            print("\nTry uploading a blueprint now!")
            break
        elif current_status == 'Failed':
            print(f"\n\n❌ Update failed!")
            if 'FailureReason' in status:
                print(f"Reason: {status['FailureReason']}")
            break
        
        time.sleep(30)  # Check every 30 seconds
        
except KeyboardInterrupt:
    print("\n\nℹ️  Update is still running in background.")
    print("Check status with: aws sagemaker describe-endpoint --endpoint-name room-detection-yolov8-endpoint")
except Exception as e:
    print(f"\n❌ Failed to update endpoint: {e}")

print("\n" + "=" * 60)

