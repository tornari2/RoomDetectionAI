#!/usr/bin/env python3
"""
Deploy YOLOv8 model to SageMaker Serverless Inference endpoint.
"""

import argparse
import boto3
import yaml
import json
import sys
from pathlib import Path
from datetime import datetime
from botocore.exceptions import ClientError


def load_config(config_path):
    """Load endpoint configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_sagemaker_role(sagemaker_client, region):
    """Get or create SageMaker execution role."""
    # Try to get default role
    try:
        # List roles and find SageMaker execution role
        iam_client = boto3.client('iam', region_name=region)
        roles = iam_client.list_roles()
        
        for role in roles['Roles']:
            if 'SageMakerExecutionRole' in role['RoleName'] or 'sagemaker' in role['RoleName'].lower():
                return role['Arn']
    except Exception as e:
        print(f"⚠️  Could not find default role: {e}")
    
    # If no role found, user must provide one
    print("❌ No SageMaker execution role found.")
    print("Please provide a role ARN using --role-arn or set it in the config file.")
    sys.exit(1)


def create_model(sagemaker_client, config, model_artifact_path, image_uri, role_arn, region):
    """Create SageMaker model."""
    model_name = config['model']['name']
    
    # Check if model already exists
    try:
        response = sagemaker_client.describe_model(ModelName=model_name)
        print(f"⚠️  Model '{model_name}' already exists. Skipping model creation.")
        return model_name
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException':
            # Model doesn't exist, create it
            pass
        else:
            raise
    
    print(f"Creating model: {model_name}")
    print(f"  Model artifact: {model_artifact_path}")
    print(f"  Image URI: {image_uri}")
    
    try:
        response = sagemaker_client.create_model(
            ModelName=model_name,
            PrimaryContainer={
                'Image': image_uri,
                'ModelDataUrl': model_artifact_path,
                'Environment': {
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_REGION': region
                }
            },
            ExecutionRoleArn=role_arn
        )
        print(f"✅ Model created successfully: {model_name}")
        return model_name
    except ClientError as e:
        print(f"❌ Error creating model: {e}")
        raise


def create_endpoint_config(sagemaker_client, config, model_name):
    """Create endpoint configuration for serverless inference."""
    endpoint_config_name = f"{config['endpoint']['name']}-config"
    
    # Check if config already exists
    try:
        response = sagemaker_client.describe_endpoint_config(EndpointConfigName=endpoint_config_name)
        print(f"⚠️  Endpoint config '{endpoint_config_name}' already exists.")
        return endpoint_config_name
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException':
            pass
        else:
            raise
    
    serverless_config = config['endpoint']['serverless_config']
    
    print(f"Creating endpoint configuration: {endpoint_config_name}")
    print(f"  Memory size: {serverless_config['memory_size_mb']} MB")
    print(f"  Max concurrency: {serverless_config['max_concurrency']}")
    
    try:
        response = sagemaker_client.create_endpoint_config(
            EndpointConfigName=endpoint_config_name,
            ProductionVariants=[{
                'VariantName': 'AllTraffic',
                'ModelName': model_name,
                'ServerlessConfig': {
                    'MemorySizeInMB': serverless_config['memory_size_mb'],
                    'MaxConcurrency': serverless_config['max_concurrency']
                }
            }]
        )
        print(f"✅ Endpoint configuration created: {endpoint_config_name}")
        return endpoint_config_name
    except ClientError as e:
        print(f"❌ Error creating endpoint config: {e}")
        raise


def create_endpoint(sagemaker_client, config, endpoint_config_name):
    """Create or update SageMaker endpoint."""
    endpoint_name = config['endpoint']['name']
    
    # Check if endpoint exists
    try:
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        endpoint_status = response['EndpointStatus']
        
        if endpoint_status == 'InService':
            print(f"⚠️  Endpoint '{endpoint_name}' already exists and is InService.")
            print("   To update, use --update flag or delete the endpoint first.")
            return endpoint_name
        elif endpoint_status in ['Creating', 'Updating']:
            print(f"⚠️  Endpoint '{endpoint_name}' is currently {endpoint_status}.")
            print("   Please wait for it to complete.")
            return endpoint_name
        else:
            # Endpoint exists but not in service, update it
            print(f"Updating endpoint: {endpoint_name}")
            response = sagemaker_client.update_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_config_name
            )
            print(f"✅ Endpoint update initiated: {endpoint_name}")
            return endpoint_name
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException':
            # Endpoint doesn't exist, create it
            pass
        else:
            raise
    
    print(f"Creating endpoint: {endpoint_name}")
    
    try:
        response = sagemaker_client.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
        print(f"✅ Endpoint creation initiated: {endpoint_name}")
        print(f"   This may take several minutes. Monitor status with:")
        print(f"   aws sagemaker describe-endpoint --endpoint-name {endpoint_name} --region {config['region']}")
        return endpoint_name
    except ClientError as e:
        print(f"❌ Error creating endpoint: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='Deploy model to SageMaker Serverless Inference')
    parser.add_argument(
        '--config',
        type=str,
        default='sagemaker/config/endpoint-config.yaml',
        help='Path to endpoint configuration YAML file'
    )
    parser.add_argument(
        '--model-artifact-path',
        type=str,
        help='S3 path to model.tar.gz (overrides config)'
    )
    parser.add_argument(
        '--image-uri',
        type=str,
        help='ECR image URI (overrides config)'
    )
    parser.add_argument(
        '--role-arn',
        type=str,
        help='IAM role ARN for SageMaker (overrides config)'
    )
    parser.add_argument(
        '--endpoint-name',
        type=str,
        help='Endpoint name (overrides config)'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update existing endpoint'
    )
    parser.add_argument(
        '--region',
        type=str,
        help='AWS region (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.region:
        config['region'] = args.region
    if args.model_artifact_path:
        config['model']['model_artifact_path'] = args.model_artifact_path
    if args.image_uri:
        config['model']['image_uri'] = args.image_uri
    if args.endpoint_name:
        config['endpoint']['name'] = args.endpoint_name
    
    region = config['region']
    
    # Initialize SageMaker client
    sagemaker_client = boto3.client('sagemaker', region_name=region)
    
    # Get IAM role
    role_arn = args.role_arn or config['iam'].get('role_arn')
    if not role_arn:
        role_arn = get_sagemaker_role(sagemaker_client, region)
    
    print("=" * 80)
    print("Deploy Model to SageMaker Serverless Inference")
    print("=" * 80)
    print(f"Region: {region}")
    print(f"Role ARN: {role_arn}")
    print("=" * 80)
    print()
    
    # Step 1: Create model
    model_name = create_model(
        sagemaker_client,
        config,
        config['model']['model_artifact_path'],
        config['model']['image_uri'],
        role_arn,
        region
    )
    
    # Step 2: Create endpoint configuration
    endpoint_config_name = create_endpoint_config(
        sagemaker_client,
        config,
        model_name
    )
    
    # Step 3: Create or update endpoint
    endpoint_name = create_endpoint(
        sagemaker_client,
        config,
        endpoint_config_name
    )
    
    print()
    print("=" * 80)
    print("✅ Deployment initiated successfully!")
    print("=" * 80)
    print(f"\nEndpoint Name: {endpoint_name}")
    print(f"\nMonitor endpoint status:")
    print(f"  aws sagemaker describe-endpoint --endpoint-name {endpoint_name} --region {region}")
    print(f"\nAWS Console:")
    print(f"  https://console.aws.amazon.com/sagemaker/home?region={region}#/endpoints/{endpoint_name}")
    print(f"\nOnce the endpoint is 'InService', you can test it with:")
    print(f"  python3 sagemaker/tests/test_inference.py --endpoint-name {endpoint_name}")


if __name__ == '__main__':
    main()

