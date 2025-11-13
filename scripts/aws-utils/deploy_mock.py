#!/usr/bin/env python3
import subprocess
import tempfile
import os
import zipfile
import boto3
import shutil

print("Deploying Lambda with MOCK DATA...")

# Create temp directory
with tempfile.TemporaryDirectory() as tmpdir:
    # Copy files
    shutil.copy('lambda/handler.py', tmpdir)
    shutil.copytree('lambda/utils', os.path.join(tmpdir, 'utils'))
    
    # Create zip
    zip_path = '/tmp/lambda_mock.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(tmpdir):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.pyc'):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, tmpdir)
                zipf.write(file_path, arcname)
    
    print(f"Created: {zip_path}")
    
    # Deploy
    client = boto3.client('lambda', region_name='us-east-2')
    with open(zip_path, 'rb') as f:
        response = client.update_function_code(
            FunctionName='room-detection-ai-handler-dev',
            ZipFile=f.read(),
            Publish=True
        )
    
    print(f"\n✅ DEPLOYED!")
    print(f"Version: {response['Version']}")
    print(f"\n🎉 Lambda now returns MOCK room detections!")
    print("\n👉 GO UPLOAD A BLUEPRINT NOW: http://localhost:5173")
    print("   You'll see 4 mock rooms drawn on your blueprint!")

