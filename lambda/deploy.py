"""
Lambda function deployment script.
Creates or updates the Lambda function with the handler code.
"""

import json
import os
import zipfile
import boto3
import subprocess
import tempfile
import shutil
from pathlib import Path
from botocore.exceptions import ClientError


def create_deployment_package(lambda_dir='lambda', output_file='lambda_deployment.zip'):
    """
    Create deployment package for Lambda function.
    Includes handler code and dependencies.
    
    Args:
        lambda_dir: Directory containing Lambda function code
        output_file: Output zip file name
        
    Returns:
        Path to deployment package
    """
    import subprocess
    import tempfile
    import shutil
    
    print(f"Creating deployment package from {lambda_dir}...")
    
    # Create temporary directory for building package
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy Lambda function code
        lambda_path = Path(lambda_dir)
        for file_path in lambda_path.rglob('*.py'):
            if file_path.name == 'deploy.py' or 'test' in str(file_path):
                continue  # Skip deploy script and test files
            relative_path = file_path.relative_to(lambda_path)
            dest_path = Path(temp_dir) / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_path)
            print(f"  Added: {relative_path}")
        
        # Note: Dependencies like Pillow and numpy should be provided via Lambda Layers
        # Only install boto3 if needed (boto3 is already available in Lambda runtime)
        # For now, we'll rely on Lambda Layers for heavy dependencies
        
        # Create zip file
        print(f"\nCreating zip file: {output_file}")
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                # Skip __pycache__ directories
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for file in files:
                    if file.endswith('.pyc'):
                        continue
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, str(arcname))
                    if len(str(arcname)) < 60:
                        print(f"  Added: {arcname}")
    
    print(f"✅ Deployment package created: {output_file}")
    print(f"   Size: {Path(output_file).stat().st_size / (1024*1024):.2f} MB")
    return output_file


def deploy_lambda_function(
    function_name: str,
    deployment_package: str,
    config_file: str = 'aws/config/lambda-config.json',
    region: str = 'us-east-2'
):
    """
    Deploy Lambda function to AWS.
    
    Args:
        function_name: Lambda function name
        deployment_package: Path to deployment zip file
        config_file: Path to Lambda configuration JSON file
        region: AWS region
    """
    lambda_client = boto3.client('lambda', region_name=region)
    
    # Load configuration
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Read deployment package
    with open(deployment_package, 'rb') as f:
        zip_file = f.read()
    
    print(f"\nDeploying Lambda function: {function_name}")
    print(f"Region: {region}")
    print(f"Runtime: {config['runtime']}")
    print(f"Handler: {config['handler']}")
    print(f"Memory: {config['memory_size']} MB")
    print(f"Timeout: {config['timeout']} seconds")
    
    try:
        # Check if function exists
        try:
            lambda_client.get_function(FunctionName=function_name)
            print(f"\n⚠️  Function '{function_name}' already exists. Updating...")
            
            # Update function code
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_file
            )
            
            # Update function configuration
            # Filter out reserved environment variables (AWS_REGION, AWS_LAMBDA_*, etc.)
            reserved_keys = ['AWS_REGION', 'AWS_LAMBDA_FUNCTION_NAME', 'AWS_LAMBDA_FUNCTION_VERSION',
                           'AWS_LAMBDA_FUNCTION_MEMORY_SIZE', 'AWS_LAMBDA_LOG_GROUP_NAME',
                           'AWS_LAMBDA_LOG_STREAM_NAME', 'AWS_EXECUTION_ENV']
            env_vars = {k: v for k, v in config['environment_variables'].items() 
                       if k not in reserved_keys}
            
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Runtime=config['runtime'],
                Handler=config['handler'],
                MemorySize=config['memory_size'],
                Timeout=config['timeout'],
                Environment={
                    'Variables': env_vars
                },
                Role=config['iam_role']
            )
            
            print(f"✅ Function '{function_name}' updated successfully!")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"\nCreating new function '{function_name}'...")
                
                # Filter out reserved environment variables
                reserved_keys = ['AWS_REGION', 'AWS_LAMBDA_FUNCTION_NAME', 'AWS_LAMBDA_FUNCTION_VERSION',
                               'AWS_LAMBDA_FUNCTION_MEMORY_SIZE', 'AWS_LAMBDA_LOG_GROUP_NAME',
                               'AWS_LAMBDA_LOG_STREAM_NAME', 'AWS_EXECUTION_ENV']
                env_vars = {k: v for k, v in config['environment_variables'].items() 
                           if k not in reserved_keys}
                
                # Create function
                lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime=config['runtime'],
                    Role=config['iam_role'],
                    Handler=config['handler'],
                    Code={'ZipFile': zip_file},
                    Description=f"Room detection image processing Lambda function",
                    Timeout=config['timeout'],
                    MemorySize=config['memory_size'],
                    Environment={
                        'Variables': env_vars
                    },
                    Tags=config.get('tags', {})
                )
                
                print(f"✅ Function '{function_name}' created successfully!")
            else:
                raise
    
    except ClientError as e:
        print(f"❌ Error deploying Lambda function: {e}")
        raise


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Lambda function for room detection')
    parser.add_argument('--function-name', default='room-detection-processor',
                        help='Lambda function name')
    parser.add_argument('--lambda-dir', default='lambda',
                        help='Directory containing Lambda function code')
    parser.add_argument('--config', default='aws/config/lambda-config.json',
                        help='Path to Lambda configuration file')
    parser.add_argument('--region', default='us-east-2',
                        help='AWS region')
    parser.add_argument('--package-only', action='store_true',
                        help='Only create deployment package, do not deploy')
    
    args = parser.parse_args()
    
    # Create deployment package
    deployment_package = create_deployment_package(args.lambda_dir)
    
    if not args.package_only:
        # Deploy to AWS
        deploy_lambda_function(
            args.function_name,
            deployment_package,
            args.config,
            args.region
        )
    else:
        print("\n✅ Deployment package created. Deploy manually or run without --package-only flag.")


if __name__ == '__main__':
    main()

