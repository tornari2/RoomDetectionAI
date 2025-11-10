#!/usr/bin/env python3
"""
Simple deployment script to update Lambda handler.
"""

import boto3
import zipfile
import io
import sys
import os

def deploy_handler(function_name='room-detection-ai-handler-dev'):
    """Deploy handler.py to Lambda function."""
    
    print("=" * 60)
    print(f"Deploying to Lambda function: {function_name}")
    print("=" * 60)
    
    # Create in-memory zip file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add handler.py
        handler_path = os.path.join(os.path.dirname(__file__), 'handler.py')
        if not os.path.exists(handler_path):
            print(f"❌ Error: handler.py not found at {handler_path}")
            sys.exit(1)
        
        print(f"Adding handler.py ({os.path.getsize(handler_path)} bytes)")
        zip_file.write(handler_path, 'handler.py')
        
        # Add utils directory if it exists
        utils_path = os.path.join(os.path.dirname(__file__), 'utils')
        if os.path.exists(utils_path):
            for root, dirs, files in os.walk(utils_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(__file__))
                        print(f"Adding {arcname}")
                        zip_file.write(file_path, arcname)
    
    # Get zip contents
    zip_buffer.seek(0)
    zip_contents = zip_buffer.read()
    
    print(f"\nCreated deployment package: {len(zip_contents)} bytes")
    
    # Upload to Lambda
    try:
        lambda_client = boto3.client('lambda')
        
        print(f"\nUploading to Lambda function '{function_name}'...")
        
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_contents,
            Publish=True
        )
        
        print("\n✓ Successfully deployed!")
        print(f"  Function ARN: {response['FunctionArn']}")
        print(f"  Version: {response['Version']}")
        print(f"  Last Modified: {response['LastModified']}")
        print(f"  Code Size: {response['CodeSize']} bytes")
        
        print("\n" + "=" * 60)
        print("Next steps:")
        print("1. Try uploading a photo through your app")
        print("2. Check CloudWatch Logs if it fails")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        print("\nMake sure AWS credentials are configured:")
        print("  aws configure")
        return False

if __name__ == '__main__':
    function_name = sys.argv[1] if len(sys.argv) > 1 else 'room-detection-ai-handler-dev'
    success = deploy_handler(function_name)
    sys.exit(0 if success else 1)

