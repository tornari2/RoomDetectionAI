#!/usr/bin/env python3
import boto3

sm = boto3.client('sagemaker', region_name='us-east-2')
response = sm.describe_endpoint(EndpointName='room-detection-yolov8-endpoint')

status = response['EndpointStatus']
print(f"Endpoint Status: {status}")

if status == 'InService':
    print("\n✅ READY TO TEST!")
    print("The endpoint is running on ml.t2.medium")
    print("\n👉 Go upload a blueprint now at: http://localhost:5173")
elif status == 'Updating':
    print("\n⏳ Still updating... (~5-10 minutes total)")
    print("Wait a few more minutes and check again.")
elif status == 'Failed':
    print("\n❌ Update failed!")
    if 'FailureReason' in response:
        print(f"Reason: {response['FailureReason']}")
else:
    print(f"\n⚠️  Unknown status: {status}")

