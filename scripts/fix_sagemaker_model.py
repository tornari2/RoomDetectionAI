#!/usr/bin/env python3
"""
Fix SageMaker model packaging by including inference.py in model.tar.gz.

This script:
1. Downloads the trained model artifacts from S3
2. Extracts the model files
3. Adds the inference.py script
4. Creates a proper requirements.txt
5. Repackages as model.tar.gz
6. Uploads to S3
7. Updates the SageMaker model
8. Updates the endpoint
"""

import boto3
import tarfile
import os
import shutil
import tempfile
from pathlib import Path
import sys

# Configuration
REGION = 'us-east-2'
S3_BUCKET = 'room-detection-ai-blueprints-dev'
ORIGINAL_MODEL_S3_KEY = 'training/outputs/yolov8-room-detection-20251108-224902/output/model.tar.gz'
NEW_MODEL_S3_KEY = 'models/room-detection-yolov8-fixed/model.tar.gz'
MODEL_NAME = 'room-detection-yolov8-model'
ENDPOINT_CONFIG_NAME = 'room-detection-yolov8-endpoint-config'
ENDPOINT_NAME = 'room-detection-yolov8-endpoint'

# Initialize clients
s3_client = boto3.client('s3', region_name=REGION)
sagemaker_client = boto3.client('sagemaker', region_name=REGION)

def download_model_from_s3(bucket, key, local_path):
    """Download model artifacts from S3."""
    print(f"\n📥 Downloading model from s3://{bucket}/{key}")
    s3_client.download_file(bucket, key, local_path)
    print(f"✅ Downloaded to {local_path}")

def extract_model(tar_path, extract_dir):
    """Extract model tar.gz file."""
    print(f"\n📦 Extracting model to {extract_dir}")
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(extract_dir)
    print(f"✅ Extracted model files")
    
    # List extracted files
    print("\nExtracted files:")
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            rel_path = os.path.relpath(file_path, extract_dir)
            print(f"  - {rel_path} ({file_size:.2f} MB)")

def create_inference_requirements():
    """Create requirements.txt for inference."""
    return """ultralytics==8.0.196
torch==2.0.1
torchvision==0.15.2
Pillow==10.0.0
numpy>=1.23.0,<1.26.0
opencv-python-headless==4.8.0.76
"""

def repackage_model(model_dir, inference_script_path, output_tar_path):
    """Repackage model with inference.py."""
    print(f"\n📦 Repackaging model with inference script")
    
    # Copy inference script to model directory
    inference_dest = os.path.join(model_dir, 'code', 'inference.py')
    os.makedirs(os.path.dirname(inference_dest), exist_ok=True)
    shutil.copy(inference_script_path, inference_dest)
    print(f"✅ Copied inference.py to model/code/")
    
    # Create requirements.txt
    requirements_path = os.path.join(model_dir, 'code', 'requirements.txt')
    with open(requirements_path, 'w') as f:
        f.write(create_inference_requirements())
    print(f"✅ Created requirements.txt")
    
    # Create tar.gz
    print(f"\n📦 Creating {output_tar_path}")
    with tarfile.open(output_tar_path, 'w:gz') as tar:
        for item in os.listdir(model_dir):
            item_path = os.path.join(model_dir, item)
            arcname = item
            tar.add(item_path, arcname=arcname)
            print(f"  - Added {item}")
    
    # Get file size
    file_size = os.path.getsize(output_tar_path) / (1024 * 1024)  # MB
    print(f"✅ Created model.tar.gz ({file_size:.2f} MB)")

def upload_model_to_s3(local_tar_path, bucket, key):
    """Upload repackaged model to S3."""
    print(f"\n📤 Uploading to s3://{bucket}/{key}")
    s3_client.upload_file(local_tar_path, bucket, key)
    print(f"✅ Uploaded model to S3")
    
    # Get S3 URL
    s3_url = f"s3://{bucket}/{key}"
    print(f"   Model URL: {s3_url}")
    return s3_url

def get_execution_role():
    """Get SageMaker execution role ARN."""
    print(f"\n🔍 Getting SageMaker execution role")
    
    # Try to get from existing model
    try:
        response = sagemaker_client.describe_model(ModelName=MODEL_NAME)
        role_arn = response['ExecutionRoleArn']
        print(f"✅ Found role: {role_arn}")
        return role_arn
    except:
        pass
    
    # If model doesn't exist, use default role
    iam = boto3.client('iam', region_name=REGION)
    account_id = boto3.client('sts').get_caller_identity()['Account']
    role_name = 'SageMakerExecutionRole'
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    print(f"✅ Using role: {role_arn}")
    return role_arn

def get_sagemaker_pytorch_image_uri():
    """Get the pre-built PyTorch inference container URI."""
    # Use AWS's pre-built PyTorch inference container
    # This supports custom inference scripts via inference.py
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    # Try to use the existing custom image first (cpu-v1)
    try:
        ecr_client = boto3.client('ecr', region_name=REGION)
        ecr_client.describe_images(
            repositoryName='room-detection-yolov8',
            imageIds=[{'imageTag': 'cpu-v1'}]
        )
        custom_image_uri = f"{account_id}.dkr.ecr.{REGION}.amazonaws.com/room-detection-yolov8:cpu-v1"
        print(f"  Using custom image: {custom_image_uri}")
        return custom_image_uri
    except:
        pass
    
    # Fallback to AWS pre-built PyTorch container
    # Format: <account>.dkr.ecr.<region>.amazonaws.com/pytorch-inference:<framework_version>-<processor>-<python_version>
    # Using PyTorch 2.0 CPU container compatible with our model
    pytorch_image_uri = f"763104351884.dkr.ecr.{REGION}.amazonaws.com/pytorch-inference:2.0.0-cpu-py310"
    print(f"  Using AWS PyTorch container: {pytorch_image_uri}")
    return pytorch_image_uri

def update_sagemaker_model(model_s3_url, role_arn):
    """Update SageMaker model with new artifacts."""
    print(f"\n🔄 Updating SageMaker model: {MODEL_NAME}")
    
    # Get image URI
    image_uri = get_sagemaker_pytorch_image_uri()
    
    # Delete existing model if it exists
    try:
        sagemaker_client.describe_model(ModelName=MODEL_NAME)
        print(f"  Deleting existing model...")
        sagemaker_client.delete_model(ModelName=MODEL_NAME)
        print(f"  ✅ Deleted existing model")
    except sagemaker_client.exceptions.ClientError:
        print(f"  No existing model to delete")
    
    # Create new model
    print(f"  Creating new model...")
    print(f"    Image: {image_uri}")
    print(f"    Model Data: {model_s3_url}")
    print(f"    Role: {role_arn}")
    
    sagemaker_client.create_model(
        ModelName=MODEL_NAME,
        PrimaryContainer={
            'Image': image_uri,
            'ModelDataUrl': model_s3_url,
            'Environment': {
                'SAGEMAKER_PROGRAM': 'inference.py',
                'SAGEMAKER_SUBMIT_DIRECTORY': model_s3_url,
                'SAGEMAKER_REGION': REGION
            }
        },
        ExecutionRoleArn=role_arn
    )
    print(f"✅ Created new SageMaker model")

def update_endpoint():
    """Update endpoint to use new model."""
    print(f"\n🔄 Updating endpoint: {ENDPOINT_NAME}")
    
    # We need to create a new endpoint config with a different name
    # Then update the endpoint to use the new config
    import time
    timestamp = int(time.time())
    new_config_name = f"{ENDPOINT_CONFIG_NAME}-{timestamp}"
    
    try:
        # Get current endpoint's config name
        endpoint_response = sagemaker_client.describe_endpoint(EndpointName=ENDPOINT_NAME)
        current_config_name = endpoint_response['EndpointConfigName']
        
        # Get current endpoint config to copy its settings
        current_config_response = sagemaker_client.describe_endpoint_config(
            EndpointConfigName=current_config_name
        )
        current_variant = current_config_response['ProductionVariants'][0]
        
        print(f"  Current config: {current_config_name}")
        print(f"  Creating new endpoint config: {new_config_name}")
        print(f"    Using model: {MODEL_NAME}")
        print(f"    Serverless config: {current_variant.get('ServerlessConfig', {})}")
        
        # Create new endpoint config with updated model
        variant_config = {
            'VariantName': current_variant['VariantName'],
            'ModelName': MODEL_NAME,
            'InitialVariantWeight': current_variant.get('InitialVariantWeight', 1.0),
        }
        
        # Add serverless config if it exists
        if 'ServerlessConfig' in current_variant:
            variant_config['ServerlessConfig'] = current_variant['ServerlessConfig']
        
        # Only add VolumeSizeInGB for non-serverless endpoints
        if 'ServerlessConfig' not in current_variant and 'VolumeSizeInGB' in current_variant:
            variant_config['VolumeSizeInGB'] = current_variant['VolumeSizeInGB']
        
        sagemaker_client.create_endpoint_config(
            EndpointConfigName=new_config_name,
            ProductionVariants=[variant_config]
        )
        print(f"✅ Created new endpoint config")
        
        # Update endpoint to use new config
        print(f"  Updating endpoint to use new config...")
        sagemaker_client.update_endpoint(
            EndpointName=ENDPOINT_NAME,
            EndpointConfigName=new_config_name
        )
        
        print(f"✅ Endpoint update initiated")
        print(f"\n⏳ Waiting for endpoint to be InService...")
        print(f"   This may take 5-10 minutes for serverless endpoint...")
        print(f"   You can continue working - the endpoint will update in the background.")
        
        # Wait for endpoint to be in service
        waiter = sagemaker_client.get_waiter('endpoint_in_service')
        waiter.wait(
            EndpointName=ENDPOINT_NAME,
            WaiterConfig={'Delay': 30, 'MaxAttempts': 40}
        )
        
        print(f"✅ Endpoint is now InService!")
        
        # Delete old endpoint config
        try:
            print(f"  Cleaning up old config: {current_config_name}")
            sagemaker_client.delete_endpoint_config(
                EndpointConfigName=current_config_name
            )
            print(f"✅ Deleted old endpoint config")
        except:
            pass  # Not critical if this fails
        
    except Exception as e:
        print(f"❌ Error updating endpoint: {e}")
        print(f"\n⚠️  The model was created successfully in S3.")
        print(f"   You can manually update the endpoint in the AWS console:")
        print(f"   1. Create new endpoint config using model: {MODEL_NAME}")
        print(f"   2. Update endpoint to use the new config")
        raise

def main():
    """Main execution function."""
    print("="*60)
    print("🔧 SageMaker Model Fix Script")
    print("="*60)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    inference_script = project_root / 'sagemaker' / 'inference.py'
    
    if not inference_script.exists():
        print(f"❌ Error: inference.py not found at {inference_script}")
        sys.exit(1)
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        
        # Step 1: Download model
        original_tar = temp_dir / 'original_model.tar.gz'
        download_model_from_s3(S3_BUCKET, ORIGINAL_MODEL_S3_KEY, str(original_tar))
        
        # Step 2: Extract model
        extract_dir = temp_dir / 'extracted'
        extract_dir.mkdir()
        extract_model(str(original_tar), str(extract_dir))
        
        # Step 3: Repackage with inference.py
        new_tar = temp_dir / 'model.tar.gz'
        repackage_model(str(extract_dir), str(inference_script), str(new_tar))
        
        # Step 4: Upload to S3
        model_s3_url = upload_model_to_s3(str(new_tar), S3_BUCKET, NEW_MODEL_S3_KEY)
        
        # Step 5: Get execution role
        role_arn = get_execution_role()
        
        # Step 6: Update SageMaker model
        update_sagemaker_model(model_s3_url, role_arn)
        
        # Step 7: Update endpoint
        update_endpoint()
    
    print("\n"+"="*60)
    print("✅ ALL DONE! SageMaker model has been fixed!")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. Test endpoint: python3 {project_root}/sagemaker/tests/test_inference.py")
    print(f"2. Test full flow: Upload a blueprint via the frontend")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

