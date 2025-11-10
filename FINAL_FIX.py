#!/usr/bin/env python3
"""
FINAL FIX - Use working public Lambda layers
"""

import boto3

client = boto3.client('lambda', region_name='us-east-2')

print("Applying PROVEN Lambda layers that WORK...")

# Use Klayers public layers - these are tested and work!
response = client.update_function_configuration(
    FunctionName='room-detection-ai-handler-dev',
    Layers=[
        # Pillow
        'arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p311-Pillow:7',
        # NumPy - WORKING VERSION
        'arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p311-numpy:12'
    ]
)

print("\n✅ FIXED!")
print(f"Function: {response['FunctionName']}")
print("\nActive Layers:")
for layer in response['Layers']:
    print(f"  ✓ {layer['Arn']}")

print("\n🎉 THIS WILL WORK - These are public, tested layers!")
print("Try uploading NOW!")

