#!/usr/bin/env python3
"""
Download and inspect the model.tar.gz
"""

import boto3
import tarfile
import tempfile
import os

s3 = boto3.client('s3', region_name='us-east-2')

bucket = 'room-detection-ai-blueprints-dev'
key = 'training/outputs/yolov8-room-detection-20251108-224902/output/model.tar.gz'

print("Downloading model.tar.gz...")
with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
    s3.download_fileobj(bucket, key, tmp)
    tmp_path = tmp.name

print(f"Downloaded to: {tmp_path}")
print("\nContents of model.tar.gz:")
print("=" * 60)

try:
    with tarfile.open(tmp_path, 'r:gz') as tar:
        members = tar.getmembers()
        
        if not members:
            print("❌ TAR FILE IS EMPTY!")
        else:
            for member in members:
                size_mb = member.size / (1024 * 1024)
                print(f"  {member.name:40s} {size_mb:8.2f} MB")
            
            # Check for model.pt
            model_files = [m for m in members if 'model.pt' in m.name or m.name.endswith('.pt')]
            
            print("\n" + "=" * 60)
            if model_files:
                print(f"✅ Found {len(model_files)} .pt file(s)")
                for f in model_files:
                    print(f"  - {f.name}")
            else:
                print("❌ NO model.pt FILE FOUND!")
                print("This is why SageMaker is crashing!")
                
finally:
    os.unlink(tmp_path)

