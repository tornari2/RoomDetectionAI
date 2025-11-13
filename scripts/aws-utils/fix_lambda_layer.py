#!/usr/bin/env python3
"""
Remove the problematic numpy Lambda layer
Run this script: python3 fix_lambda_layer.py
"""

import boto3
import sys

def main():
    client = boto3.client('lambda', region_name='us-east-2')
    
    print("Removing problematic numpy layer from Lambda function...")
    
    try:
        response = client.update_function_configuration(
            FunctionName='room-detection-ai-handler-dev',
            Layers=[
                'arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p311-Pillow:7'
            ]
        )
        
        print("\n✅ SUCCESS!")
        print(f"Function: {response['FunctionName']}")
        print(f"Runtime: {response['Runtime']}")
        print("\nActive Layers:")
        for layer in response.get('Layers', []):
            print(f"  - {layer['Arn']}")
        
        print("\n🎉 The numpy import error should now be fixed!")
        print("Try uploading a blueprint again.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

