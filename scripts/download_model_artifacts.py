#!/usr/bin/env python3
"""
Download model artifacts from S3 for a completed SageMaker training job.
"""

import argparse
import boto3
import os
import tarfile
from pathlib import Path
from botocore.exceptions import ClientError


def download_from_s3(s3_path, local_path, region='us-east-2'):
    """Download a file from S3."""
    s3_client = boto3.client('s3', region_name=region)
    
    # Parse S3 path
    if not s3_path.startswith('s3://'):
        raise ValueError(f"Invalid S3 path: {s3_path}")
    
    s3_path = s3_path[5:]  # Remove 's3://'
    bucket, key = s3_path.split('/', 1)
    
    print(f"Downloading: s3://{bucket}/{key}")
    print(f"To: {local_path}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    try:
        s3_client.download_file(bucket, key, local_path)
        print(f"✅ Downloaded successfully")
        return True
    except ClientError as e:
        print(f"❌ Error downloading: {e}")
        return False


def extract_tar(tar_path, extract_to):
    """Extract a tar.gz file."""
    print(f"\nExtracting: {tar_path}")
    print(f"To: {extract_to}")
    
    os.makedirs(extract_to, exist_ok=True)
    
    try:
        with tarfile.open(tar_path, 'r:gz') as tar:
            tar.extractall(extract_to)
        print(f"✅ Extracted successfully")
        return True
    except Exception as e:
        print(f"❌ Error extracting: {e}")
        return False


def list_extracted_files(extract_dir):
    """List files in the extracted directory."""
    print(f"\n📁 Extracted files:")
    print("=" * 80)
    
    for root, dirs, files in os.walk(extract_dir):
        level = root.replace(extract_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            size_str = f"{file_size / 1024 / 1024:.2f} MB" if file_size > 1024 * 1024 else f"{file_size / 1024:.2f} KB"
            print(f"{subindent}{file} ({size_str})")


def main():
    parser = argparse.ArgumentParser(description='Download model artifacts from S3')
    parser.add_argument(
        '--job-name',
        type=str,
        default='yolov8-room-detection-20251108-224902',
        help='Training job name (default: yolov8-room-detection-20251108-224902)'
    )
    parser.add_argument(
        '--s3-path',
        type=str,
        help='Full S3 path to model.tar.gz (overrides job-name)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='sagemaker/outputs/model_artifacts',
        help='Local directory to save artifacts (default: sagemaker/outputs/model_artifacts)'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-2',
        help='AWS region (default: us-east-2)'
    )
    parser.add_argument(
        '--extract',
        action='store_true',
        help='Extract the model.tar.gz file after downloading'
    )
    parser.add_argument(
        '--bucket',
        type=str,
        default='room-detection-ai-blueprints-dev',
        help='S3 bucket name (default: room-detection-ai-blueprints-dev)'
    )
    
    args = parser.parse_args()
    
    # Determine S3 path
    if args.s3_path:
        s3_path = args.s3_path
    else:
        s3_path = f"s3://{args.bucket}/training/outputs/{args.job_name}/output/model.tar.gz"
    
    # Local paths
    output_dir = Path(args.output_dir)
    tar_filename = f"{args.job_name}_model.tar.gz"
    local_tar_path = output_dir / tar_filename
    extract_dir = output_dir / args.job_name
    
    print("=" * 80)
    print("Download Model Artifacts from S3")
    print("=" * 80)
    print(f"Job Name: {args.job_name}")
    print(f"S3 Path: {s3_path}")
    print(f"Output Directory: {output_dir}")
    print(f"Region: {args.region}")
    print("=" * 80)
    print()
    
    # Download
    success = download_from_s3(s3_path, str(local_tar_path), args.region)
    
    if not success:
        print("\n❌ Download failed. Exiting.")
        return
    
    # Extract if requested
    if args.extract:
        print()
        extract_success = extract_tar(str(local_tar_path), str(extract_dir))
        if extract_success:
            list_extracted_files(str(extract_dir))
    else:
        print(f"\n💡 To extract the model, run:")
        print(f"   tar -xzf {local_tar_path} -C {extract_dir}")
    
    print("\n" + "=" * 80)
    print("✅ Download complete!")
    print("=" * 80)
    print(f"\nModel artifacts:")
    print(f"  Archive: {local_tar_path}")
    if args.extract:
        print(f"  Extracted: {extract_dir}")


if __name__ == '__main__':
    main()

