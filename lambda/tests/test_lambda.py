#!/usr/bin/env python3
"""
Test Lambda function locally or invoke it on AWS.
"""

import json
import sys
import boto3
import argparse
from pathlib import Path

# Add parent directory to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from handler import lambda_handler


def test_locally(event_file: str):
    """Test Lambda function locally."""
    print("=" * 80)
    print("Testing Lambda Function Locally")
    print("=" * 80)
    
    # Load test event
    with open(event_file, 'r') as f:
        event = json.load(f)
    
    print(f"\nTest Event:")
    print(json.dumps(event, indent=2))
    print("\n" + "=" * 80)
    print("Invoking Lambda handler...")
    print("=" * 80 + "\n")
    
    try:
        # Invoke handler
        response = lambda_handler(event, None)
        
        # Print response
        print("Response:")
        print("-" * 80)
        if isinstance(response.get('body'), str):
            body = json.loads(response['body'])
            print(json.dumps(body, indent=2))
        else:
            print(json.dumps(response, indent=2))
        print("-" * 80)
        
        print(f"\nStatus Code: {response.get('statusCode', 'N/A')}")
        
        if response.get('statusCode') == 200:
            print("✅ Lambda function executed successfully!")
        else:
            print("❌ Lambda function returned an error")
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        import traceback
        traceback.print_exc()


def test_on_aws(function_name: str, event_file: str, region: str = 'us-east-2'):
    """Invoke Lambda function on AWS."""
    print("=" * 80)
    print("Testing Lambda Function on AWS")
    print("=" * 80)
    
    lambda_client = boto3.client('lambda', region_name=region)
    
    # Load test event
    with open(event_file, 'r') as f:
        event = json.load(f)
    
    print(f"\nFunction Name: {function_name}")
    print(f"Region: {region}")
    print(f"\nTest Event:")
    print(json.dumps(event, indent=2))
    print("\n" + "=" * 80)
    print("Invoking Lambda function...")
    print("=" * 80 + "\n")
    
    try:
        # Invoke function
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',  # Synchronous invocation
            Payload=json.dumps(event)
        )
        
        # Read response
        response_payload = json.loads(response['Payload'].read())
        
        print("Response:")
        print("-" * 80)
        print(json.dumps(response_payload, indent=2))
        print("-" * 80)
        
        # Check for errors
        if 'errorMessage' in response_payload:
            print(f"\n❌ Lambda function error: {response_payload['errorMessage']}")
            if 'stackTrace' in response_payload:
                print("\nStack Trace:")
                for line in response_payload['stackTrace']:
                    print(f"  {line}")
        else:
            print("\n✅ Lambda function executed successfully!")
            
    except Exception as e:
        print(f"❌ Error invoking Lambda function: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description='Test Lambda function')
    parser.add_argument('--event-file', default='lambda/tests/test_event.json',
                        help='Path to test event JSON file')
    parser.add_argument('--function-name', default='room-detection-processor',
                        help='Lambda function name (for AWS testing)')
    parser.add_argument('--region', default='us-east-2',
                        help='AWS region')
    parser.add_argument('--local', action='store_true',
                        help='Test locally (requires AWS credentials and S3 access)')
    parser.add_argument('--aws', action='store_true',
                        help='Test on AWS Lambda')
    
    args = parser.parse_args()
    
    if args.local:
        test_locally(args.event_file)
    elif args.aws:
        test_on_aws(args.function_name, args.event_file, args.region)
    else:
        print("Please specify --local or --aws")
        print("\nExamples:")
        print("  python3 lambda/tests/test_lambda.py --local")
        print("  python3 lambda/tests/test_lambda.py --aws")


if __name__ == '__main__':
    main()

