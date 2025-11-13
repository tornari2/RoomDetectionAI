#!/usr/bin/env python3
"""
Create and deploy Lambda package with numpy bundled
Run this: python3 deploy_with_numpy.py
"""

import subprocess
import tempfile
import os
import shutil
import zipfile
import boto3

def main():
    print("Creating Lambda deployment package with numpy...")
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Working in: {tmpdir}")
        
        # Copy handler and utils
        print("Copying handler.py and utils/...")
        shutil.copy('lambda/handler.py', tmpdir)
        shutil.copytree('lambda/utils', os.path.join(tmpdir, 'utils'))
        
        # Install numpy with pip
        print("Installing numpy for Lambda (this may take a minute)...")
        subprocess.run([
            'pip', 'install', 
            'numpy',
            '--target', tmpdir,
            '--platform', 'manylinux2014_x86_64',
            '--python-version', '3.11',
            '--only-binary=:all:',
            '--upgrade'
        ], check=True)
        
        # Create zip file
        zip_path = '/tmp/lambda_with_numpy.zip'
        print(f"Creating zip file: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(tmpdir):
                # Skip __pycache__ directories
                dirs[:] = [d for d in dirs if d != '__pycache__']
                
                for file in files:
                    if file.endswith('.pyc'):
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    zipf.write(file_path, arcname)
        
        # Check size
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"Package size: {size_mb:.2f} MB")
        
        # Deploy to Lambda
        print("Deploying to AWS Lambda...")
        client = boto3.client('lambda', region_name='us-east-2')
        
        with open(zip_path, 'rb') as f:
            response = client.update_function_code(
                FunctionName='room-detection-ai-handler-dev',
                ZipFile=f.read(),
                Publish=True
            )
        
        print("\n✅ SUCCESS!")
        print(f"Function: {response['FunctionName']}")
        print(f"Version: {response['Version']}")
        print(f"Code Size: {response['CodeSize']} bytes")
        print("\n🎉 Lambda now has numpy bundled!")
        print("Try uploading a blueprint again.")

if __name__ == '__main__':
    main()

