#!/usr/bin/env python3
"""
Alternative deployment using SageMaker Python SDK Model class.
This may handle Docker manifest format conversion automatically.
"""

import argparse
import yaml
import boto3
import sagemaker
from sagemaker import Model
from sagemaker.serverless import ServerlessInferenceConfig


def load_config(config_path):
    """Load endpoint configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def deploy_with_sdk(config_path):
    """Deploy using SageMaker Python SDK."""
    config = load_config(config_path)
    
    # Get configuration values
    model_artifact_path = config['model']['model_artifact_path']
    image_uri = config['model']['image_uri']
    role_arn = config['iam']['role_arn']
    endpoint_name = config['endpoint']['name']
    region = config['region']
    serverless_config = config['endpoint']['serverless_config']
    
    print("=" * 80)
    print("Deploy Model using SageMaker Python SDK")
    print("=" * 80)
    print(f"Region: {region}")
    print(f"Role ARN: {role_arn}")
    print(f"Endpoint Name: {endpoint_name}")
    print(f"Image URI: {image_uri}")
    print(f"Model Artifact: {model_artifact_path}")
    print("=" * 80)
    print()
    
    # Create SageMaker session
    boto_session = boto3.Session(region_name=region)
    sagemaker_session = sagemaker.Session(boto_session=boto_session)
    
    # Create Model
    print("Creating SageMaker Model...")
    model = Model(
        image_uri=image_uri,
        model_data=model_artifact_path,
        role=role_arn,
        env={
            'SAGEMAKER_PROGRAM': 'inference.py',
            'SAGEMAKER_REGION': region
        },
        sagemaker_session=sagemaker_session
    )
    
    # Create serverless config
    serverless_inference_config = ServerlessInferenceConfig(
        memory_size_in_mb=serverless_config['memory_size_mb'],
        max_concurrency=serverless_config['max_concurrency']
    )
    
    # Deploy endpoint
    print(f"\nDeploying endpoint: {endpoint_name}")
    print("This may take several minutes...")
    
    try:
        predictor = model.deploy(
            endpoint_name=endpoint_name,
            serverless_inference_config=serverless_inference_config,
            wait=False  # Don't wait, return immediately
        )
        
        print(f"\n✅ Deployment initiated!")
        print(f"\nEndpoint Name: {endpoint_name}")
        print(f"\nMonitor endpoint status:")
        print(f"  aws sagemaker describe-endpoint --endpoint-name {endpoint_name} --region {region}")
        print(f"\nAWS Console:")
        print(f"  https://console.aws.amazon.com/sagemaker/home?region={region}#/endpoints/{endpoint_name}")
        
        return endpoint_name
        
    except Exception as e:
        print(f"\n❌ Error deploying: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='Deploy model using SageMaker Python SDK')
    parser.add_argument(
        '--config',
        type=str,
        default='sagemaker/config/endpoint-config.yaml',
        help='Path to endpoint configuration YAML file'
    )
    
    args = parser.parse_args()
    
    deploy_with_sdk(args.config)


if __name__ == '__main__':
    main()

