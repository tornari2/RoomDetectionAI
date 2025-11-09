#!/usr/bin/env python3
"""
Create and trigger AWS CodeBuild project to build Docker image.
This solves the Docker manifest format issue by building on Linux.
"""

import argparse
import boto3
import json
from botocore.exceptions import ClientError


def create_codebuild_project(codebuild_client, project_name, region='us-east-2'):
    """Create CodeBuild project if it doesn't exist."""
    # Configuration
    ecr_registry = "971422717446.dkr.ecr.us-east-2.amazonaws.com"
    repository = "room-detection-yolov8"
    
    project_config = {
        'name': project_name,
        'description': 'Build Docker image for SageMaker YOLOv8 inference',
        'source': {
            'type': 'S3',
            'location': f'room-detection-ai-blueprints-dev/codebuild/source.zip',  # Will be uploaded
        },
        'artifacts': {
            'type': 'NO_ARTIFACTS'
        },
        'environment': {
            'type': 'LINUX_CONTAINER',
            'image': 'aws/codebuild/standard:7.0',  # Latest CodeBuild image with Docker
            'computeType': 'BUILD_GENERAL1_SMALL',
            'privilegedMode': True,  # Required for Docker
            'environmentVariables': [
                {
                    'name': 'AWS_DEFAULT_REGION',
                    'value': region
                },
                {
                    'name': 'ECR_REGISTRY',
                    'value': ecr_registry
                },
                {
                    'name': 'REPOSITORY',
                    'value': repository
                }
            ]
        },
        'serviceRole': f'arn:aws:iam::971422717446:role/service-role/AmazonSageMaker-ExecutionRole-20250802T111914',  # Use existing SageMaker role
        'timeoutInMinutes': 30
    }
    
    try:
        # Check if project exists
        try:
            codebuild_client.batch_get_projects(names=[project_name])
            print(f"⚠️  CodeBuild project '{project_name}' already exists.")
            return project_name
        except ClientError:
            pass
        
        # Create project
        print(f"Creating CodeBuild project: {project_name}")
        response = codebuild_client.create_project(**project_config)
        print(f"✅ CodeBuild project created: {project_name}")
        return project_name
        
    except ClientError as e:
        print(f"❌ Error creating CodeBuild project: {e}")
        raise


def upload_source_to_s3(s3_client, bucket, source_zip_path):
    """Upload source code to S3 for CodeBuild."""
    key = 'codebuild/source.zip'
    
    print(f"Uploading source to s3://{bucket}/{key}")
    try:
        s3_client.upload_file(source_zip_path, bucket, key)
        print(f"✅ Source uploaded successfully")
        return f's3://{bucket}/{key}'
    except Exception as e:
        print(f"❌ Error uploading source: {e}")
        raise


def start_build(codebuild_client, project_name, s3_source_location):
    """Start CodeBuild build."""
    print(f"\nStarting CodeBuild build for project: {project_name}")
    
    try:
        response = codebuild_client.start_build(
            projectName=project_name,
            sourceLocationOverride=s3_source_location
        )
        
        build_id = response['build']['id']
        print(f"✅ Build started: {build_id}")
        print(f"\nMonitor build status:")
        print(f"  aws codebuild batch-get-builds --ids {build_id} --region us-east-2")
        print(f"\nAWS Console:")
        print(f"  https://console.aws.amazon.com/codesuite/codebuild/projects/{project_name}/build/{build_id}")
        
        return build_id
        
    except ClientError as e:
        print(f"❌ Error starting build: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='Build Docker image using AWS CodeBuild')
    parser.add_argument(
        '--project-name',
        type=str,
        default='room-detection-docker-build',
        help='CodeBuild project name'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-2',
        help='AWS region'
    )
    parser.add_argument(
        '--create-project-only',
        action='store_true',
        help='Only create the CodeBuild project, do not start build'
    )
    
    args = parser.parse_args()
    
    # Initialize clients
    codebuild_client = boto3.client('codebuild', region_name=args.region)
    s3_client = boto3.client('s3', region_name=args.region)
    
    print("=" * 80)
    print("Build Docker Image using AWS CodeBuild")
    print("=" * 80)
    print(f"Region: {args.region}")
    print(f"Project Name: {args.project_name}")
    print("=" * 80)
    print()
    
    # Create CodeBuild project
    project_name = create_codebuild_project(codebuild_client, args.project_name, args.region)
    
    if args.create_project_only:
        print("\n✅ CodeBuild project created. You can now trigger builds manually or via CI/CD.")
        return
    
    # For now, provide instructions for manual source upload
    print("\n" + "=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("1. Create a source zip file:")
    print("   cd /Users/michaeltornaritis/Desktop/WK4_RoomDetectionAI")
    print("   zip -r /tmp/source.zip sagemaker/ buildspec.yml -x '*.git*' '*.pyc' '__pycache__/*'")
    print()
    print("2. Upload to S3:")
    print("   aws s3 cp /tmp/source.zip s3://room-detection-ai-blueprints-dev/codebuild/source.zip")
    print()
    print("3. Start build:")
    print(f"   aws codebuild start-build --project-name {project_name} --region {args.region}")
    print()
    print("Or use the simplified script:")
    print("   python3 scripts/build_with_codebuild.py --start-build")


if __name__ == '__main__':
    main()

