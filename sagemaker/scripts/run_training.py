#!/usr/bin/env python3
"""
SageMaker Training Job Launcher
Creates and launches a SageMaker training job for YOLOv8 room detection model.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import boto3
import yaml
import sagemaker
from sagemaker import get_execution_role
from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput


def load_config(config_path):
    """Load training configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def create_hyperparameters(config):
    """Extract hyperparameters from config and convert to SageMaker format."""
    hyperparams = config['training']['hyperparameters']
    
    # Convert to strings (SageMaker requires string values)
    hyperparams_str = {}
    for key, value in hyperparams.items():
        if isinstance(value, bool):
            hyperparams_str[key] = str(value).lower()
        else:
            hyperparams_str[key] = str(value)
    
    return hyperparams_str


def create_training_job_name(base_name='yolov8-room-detection'):
    """Generate unique training job name with timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    return f"{base_name}-{timestamp}"


def create_estimator(config, role, image_uri, base_job_name='yolov8-training', region='us-east-2'):
    """Create SageMaker Estimator with configuration."""
    training_config = config['training']
    s3_config = config['s3']
    
    # Get hyperparameters and add sagemaker_program to specify entry point
    hyperparameters = create_hyperparameters(config)
    hyperparameters['sagemaker_program'] = 'train.py'  # Explicitly set entry point script
    
    # Create Estimator
    estimator = Estimator(
        image_uri=image_uri,
        role=role,
        instance_count=training_config['instance_count'],
        instance_type=training_config['instance_type'],
        volume_size=training_config['volume_size_gb'],
        max_run=training_config['max_runtime_hours'] * 3600,  # Convert hours to seconds
        # Note: max_wait is only supported with Spot Training, so we don't set it here
        output_path=f"s3://{s3_config['bucket']}/{s3_config['output_prefix']}",
        hyperparameters=hyperparameters,
        base_job_name=base_job_name,
        tags=[
            {'Key': 'Project', 'Value': 'RoomDetectionAI'},
            {'Key': 'Model', 'Value': 'YOLOv8'},
            {'Key': 'Task', 'Value': 'Task5'},
        ],
        enable_network_isolation=False,  # Allow internet access for model downloads
    )
    
    return estimator


def main():
    parser = argparse.ArgumentParser(description='Launch SageMaker Training Job')
    parser.add_argument(
        '--config',
        type=str,
        default='sagemaker/config/training-config.yaml',
        help='Path to training configuration YAML file'
    )
    parser.add_argument(
        '--image-uri',
        type=str,
        help='ECR image URI (overrides config if provided)'
    )
    parser.add_argument(
        '--role',
        type=str,
        help='SageMaker execution role ARN (auto-detected if not provided)'
    )
    parser.add_argument(
        '--job-name',
        type=str,
        help='Training job name (auto-generated if not provided)'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-2',
        help='AWS region for SageMaker (default: us-east-2)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print configuration without launching job'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"📋 Loading configuration from: {config_path}")
    config = load_config(config_path)
    
    # Get image URI
    if args.image_uri:
        image_uri = args.image_uri
    else:
        container_config = config['container']
        if container_config['image_uri']:
            image_uri = container_config['image_uri']
        else:
            # Construct from registry, repository, and tag
            registry = container_config['registry']
            repository = container_config['repository']
            tag = container_config['tag']
            image_uri = f"{registry}/{repository}:{tag}"
    
    print(f"🐳 Container image: {image_uri}")
    
    # Get SageMaker role
    if args.role:
        role = args.role
    else:
        try:
            role = get_execution_role()
            print(f"✅ Using SageMaker execution role: {role}")
        except Exception as e:
            print(f"❌ Could not get SageMaker execution role: {e}", file=sys.stderr)
            print("   Please provide --role argument or configure SageMaker role", file=sys.stderr)
            sys.exit(1)
    
    # Get S3 paths
    s3_config = config['s3']
    bucket = s3_config['bucket']
    
    # Normalize prefixes: remove trailing slashes and ensure no double slashes
    def normalize_prefix(prefix):
        """Normalize S3 prefix to avoid double slashes."""
        if not prefix:
            return ''
        # Remove leading slash if present
        prefix = prefix.lstrip('/')
        # Remove trailing slash
        prefix = prefix.rstrip('/')
        return prefix
    
    training_prefix = normalize_prefix(s3_config['training_prefix'])
    validation_prefix = normalize_prefix(s3_config['validation_prefix'])
    
    # Construct URIs without double slashes
    training_data_uri = f"s3://{bucket}/{training_prefix}" if training_prefix else f"s3://{bucket}"
    validation_data_uri = f"s3://{bucket}/{validation_prefix}" if validation_prefix else f"s3://{bucket}"
    
    print(f"📦 Training data: {training_data_uri}")
    print(f"📦 Validation data: {validation_data_uri}")
    
    # Create training job name
    job_name = args.job_name or create_training_job_name()
    print(f"🏷️  Training job name: {job_name}")
    
    # Print hyperparameters
    hyperparams = create_hyperparameters(config)
    print("\n📊 Hyperparameters:")
    for key, value in sorted(hyperparams.items()):
        print(f"   {key}: {value}")
    
    # Print instance configuration
    training_config = config['training']
    print(f"\n💻 Instance configuration:")
    print(f"   Type: {training_config['instance_type']}")
    print(f"   Count: {training_config['instance_count']}")
    print(f"   Volume size: {training_config['volume_size_gb']} GB")
    print(f"   Max runtime: {training_config['max_runtime_hours']} hours")
    
    # Cost estimation
    cost_config = config.get('cost_estimation', {})
    if cost_config:
        hourly_rate = cost_config.get('instance_hourly_rate_usd', 0)
        estimated_hours = cost_config.get('estimated_training_hours', 0)
        estimated_cost = cost_config.get('estimated_total_cost_usd', 0)
        print(f"\n💰 Cost estimation:")
        print(f"   Hourly rate: ${hourly_rate:.3f}")
        print(f"   Estimated time: {estimated_hours} hours")
        print(f"   Estimated cost: ${estimated_cost:.2f}")
    
    if args.dry_run:
        print("\n✅ Dry run complete. Configuration validated.")
        print("   Remove --dry-run flag to launch the training job.")
        return
    
    # Create Estimator
    print("\n🚀 Creating SageMaker Estimator...")
    base_job_name = job_name.rsplit('-', 1)[0] if '-' in job_name else 'yolov8-training'
    
    # Set SageMaker session region
    sagemaker_session = sagemaker.Session(boto_session=boto3.Session(region_name=args.region))
    
    estimator = create_estimator(config, role, image_uri, base_job_name, args.region)
    estimator.sagemaker_session = sagemaker_session
    
    # Define input channels using TrainingInput to properly handle S3 paths
    # This ensures paths are normalized and avoids double-slash issues
    inputs = {
        'training': TrainingInput(
            s3_data=training_data_uri,
            content_type='application/x-image',
            s3_data_type='S3Prefix',
            input_mode='File'
        ),
        'validation': TrainingInput(
            s3_data=validation_data_uri,
            content_type='application/x-image',
            s3_data_type='S3Prefix',
            input_mode='File'
        ),
    }
    
    # Launch training job
    print(f"\n🚀 Launching training job: {job_name}")
    print("   This may take a few moments...")
    
    try:
        estimator.fit(
            inputs=inputs,
            job_name=job_name,
            wait=False,  # Don't wait for completion (allows script to return)
            logs=False,   # Don't stream logs (can be enabled for debugging)
        )
        
        print(f"\n✅ Training job launched successfully!")
        print(f"\n📊 Job Details:")
        print(f"   Job Name: {job_name}")
        # Construct ARN from job name and region
        account_id = boto3.client('sts').get_caller_identity()['Account']
        job_arn = f"arn:aws:sagemaker:{args.region}:{account_id}:training-job/{job_name}"
        print(f"   Job ARN: {job_arn}")
        print(f"\n🔍 Monitor your training job:")
        print(f"   AWS Console: https://console.aws.amazon.com/sagemaker/home?region={args.region}#/jobs/{job_name}")
        print(f"   CloudWatch Logs: Check /aws/sagemaker/TrainingJobs/{job_name}")
        print(f"\n💡 To check status:")
        print(f"   aws sagemaker describe-training-job --training-job-name {job_name} --region {args.region}")
        print(f"\n💡 To wait for completion:")
        print(f"   aws sagemaker wait training-job-completed-or-stopped --training-job-name {job_name} --region {args.region}")
        
    except Exception as e:
        print(f"\n❌ Failed to launch training job: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

