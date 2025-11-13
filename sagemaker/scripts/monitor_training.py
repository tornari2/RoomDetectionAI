#!/usr/bin/env python3
"""
SageMaker Training Job Monitor
Monitor training job progress, metrics, and logs.
"""

import argparse
import json
import sys
import time
from datetime import datetime

import boto3
from botocore.exceptions import ClientError


def format_duration(seconds):
    """Format duration in seconds to human-readable format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def list_training_jobs(sagemaker_client, max_results=10):
    """List recent training jobs."""
    try:
        response = sagemaker_client.list_training_jobs(MaxResults=max_results, SortBy='CreationTime', SortOrder='Descending')
        return response.get('TrainingJobSummaries', [])
    except ClientError as e:
        print(f"❌ Error listing training jobs: {e}", file=sys.stderr)
        return []


def get_job_status(sagemaker_client, job_name):
    """Get training job status and details."""
    try:
        response = sagemaker_client.describe_training_job(TrainingJobName=job_name)
        return response
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error'].get('Message', '')
        
        # Handle both ValidationException and ResourceNotFound errors
        if error_code in ['ValidationException', 'ResourceNotFound'] or 'not found' in error_message.lower():
            print(f"❌ Training job '{job_name}' not found.", file=sys.stderr)
            print(f"\n💡 Available training jobs:", file=sys.stderr)
            
            # List recent jobs to help user find the correct name
            recent_jobs = list_training_jobs(sagemaker_client, max_results=10)
            if recent_jobs:
                print("   Recent training jobs:", file=sys.stderr)
                for job in recent_jobs[:5]:  # Show top 5
                    status = job.get('TrainingJobStatus', 'Unknown')
                    created = job.get('CreationTime', '')
                    print(f"   - {job['TrainingJobName']} ({status}) - Created: {created}", file=sys.stderr)
            else:
                print("   No training jobs found.", file=sys.stderr)
            
            print(f"\n   To list all jobs, use:", file=sys.stderr)
            print(f"   aws sagemaker list-training-jobs --region <your-region>", file=sys.stderr)
            sys.exit(1)
        else:
            raise


def print_job_info(job_details):
    """Print training job information."""
    job_name = job_details['TrainingJobName']
    status = job_details['TrainingJobStatus']
    creation_time = job_details['CreationTime']
    
    # Calculate elapsed time
    elapsed = (datetime.now(creation_time.tzinfo) - creation_time).total_seconds()
    
    print("=" * 80)
    print(f"Training Job: {job_name}")
    print("=" * 80)
    print(f"Status: {status}")
    print(f"Created: {creation_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Elapsed: {format_duration(elapsed)}")
    
    if 'TrainingStartTime' in job_details:
        training_start = job_details['TrainingStartTime']
        training_elapsed = (datetime.now(training_start.tzinfo) - training_start).total_seconds()
        print(f"Training started: {training_start.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Training time: {format_duration(training_elapsed)}")
    
    if 'TrainingEndTime' in job_details:
        training_end = job_details['TrainingEndTime']
        print(f"Completed: {training_end.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    print(f"\nInstance: {job_details.get('ResourceConfig', {}).get('InstanceType', 'N/A')}")
    print(f"Instance count: {job_details.get('ResourceConfig', {}).get('InstanceCount', 'N/A')}")
    
    # Hyperparameters
    if 'HyperParameters' in job_details:
        print("\nHyperparameters:")
        for key, value in sorted(job_details['HyperParameters'].items()):
            print(f"  {key}: {value}")
    
    # Metrics
    if 'FinalMetricDataList' in job_details and job_details['FinalMetricDataList']:
        print("\nFinal Metrics:")
        for metric in job_details['FinalMetricDataList']:
            metric_name = metric['MetricName']
            metric_value = metric['Value']
            timestamp = metric['Timestamp']
            print(f"  {metric_name}: {metric_value:.4f} (at {timestamp.strftime('%H:%M:%S')})")
    
    # Outputs
    if 'ModelArtifacts' in job_details:
        print(f"\nModel artifacts: {job_details['ModelArtifacts']['S3ModelArtifacts']}")
    
    # Logs
    if 'LogGroupName' in job_details:
        log_group = job_details['LogGroupName']
        log_stream = job_details.get('LogStreamName', '')
        print(f"\nCloudWatch Logs:")
        print(f"  Log Group: {log_group}")
        if log_stream:
            print(f"  Log Stream: {log_stream}")
        region = job_details.get('Region', 'us-east-1')
        print(f"  Console: https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups/log-group/{log_group.replace('/', '$252F')}")
    
    # Failure reason
    if status == 'Failed' and 'FailureReason' in job_details:
        print(f"\n❌ Failure Reason:")
        print(f"   {job_details['FailureReason']}")
    
    print("=" * 80)
    
    return status


def watch_job(sagemaker_client, job_name, interval=30):
    """Watch training job and print updates."""
    print(f"👀 Watching training job: {job_name}")
    print(f"   Update interval: {interval} seconds")
    print(f"   Press Ctrl+C to stop watching\n")
    
    last_status = None
    try:
        while True:
            job_details = get_job_status(sagemaker_client, job_name)
            status = job_details['TrainingJobStatus']
            
            if status != last_status:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Status changed: {last_status} → {status}")
                last_status = status
            
            # Print metrics if available
            if 'FinalMetricDataList' in job_details and job_details['FinalMetricDataList']:
                metrics = job_details['FinalMetricDataList']
                if metrics:
                    latest = max(metrics, key=lambda x: x['Timestamp'])
                    print(f"  Latest metric: {latest['MetricName']} = {latest['Value']:.4f}")
            
            # Check if job is complete
            if status in ['Completed', 'Failed', 'Stopped']:
                print(f"\n✅ Job finished with status: {status}")
                print_job_info(job_details)
                break
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Watching stopped by user")
        print_job_info(get_job_status(sagemaker_client, job_name))


def main():
    parser = argparse.ArgumentParser(description='Monitor SageMaker Training Job')
    parser.add_argument(
        '--job-name',
        type=str,
        help='Training job name (required unless --list is used)'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Watch job continuously (updates every 30 seconds)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Update interval in seconds when watching (default: 30)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List recent training jobs instead of monitoring a specific job'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=10,
        help='Maximum number of jobs to list (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Create SageMaker client
    sagemaker_client = boto3.client('sagemaker', region_name=args.region)
    
    # Handle list command
    if args.list:
        print("📋 Recent Training Jobs:")
        print("=" * 80)
        jobs = list_training_jobs(sagemaker_client, max_results=args.max_results)
        if jobs:
            for job in jobs:
                name = job['TrainingJobName']
                status = job.get('TrainingJobStatus', 'Unknown')
                created = job.get('CreationTime', '')
                if isinstance(created, datetime):
                    created_str = created.strftime('%Y-%m-%d %H:%M:%S UTC')
                else:
                    created_str = str(created)
                print(f"  {name}")
                print(f"    Status: {status}")
                print(f"    Created: {created_str}")
                print()
        else:
            print("  No training jobs found.")
        return
    
    # Validate job-name is provided when not listing
    if not args.job_name:
        parser.error("--job-name is required unless --list is used")
    
    # Get job status
    job_details = get_job_status(sagemaker_client, args.job_name)
    
    if args.watch:
        watch_job(sagemaker_client, args.job_name, args.interval)
    else:
        print_job_info(job_details)
        
        # Print next steps
        status = job_details['TrainingJobStatus']
        if status == 'InProgress':
            print("\n💡 To watch this job continuously:")
            print(f"   python3 sagemaker/scripts/monitor_training.py --job-name {args.job_name} --watch")
        elif status == 'Completed':
            print("\n✅ Training completed successfully!")
            print("   Next steps:")
            print("   1. Download model artifacts from S3")
            print("   2. Evaluate model performance")
            print("   3. Deploy model to endpoint (Task 6)")


if __name__ == '__main__':
    main()

