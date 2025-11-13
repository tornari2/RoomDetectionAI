#!/usr/bin/env python3
"""
Fetch CloudWatch logs for a SageMaker training job.
"""

import argparse
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import time

def get_log_streams(log_group, job_name, region='us-east-2'):
    """Get log streams for a training job."""
    logs_client = boto3.client('logs', region_name=region)
    
    try:
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            logStreamNamePrefix=f"{job_name}/",
            limit=10
        )
        # Sort by last event time manually
        streams = response.get('logStreams', [])
        streams.sort(key=lambda x: x.get('lastEventTimestamp', 0), reverse=True)
        return streams
    except ClientError as e:
        print(f"❌ Error getting log streams: {e}")
        return []

def fetch_logs(log_group, log_stream, region='us-east-2', limit=100):
    """Fetch logs from a specific stream."""
    logs_client = boto3.client('logs', region_name=region)
    
    try:
        response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            limit=limit,
            startFromHead=False  # Get most recent logs
        )
        return response.get('events', [])
    except ClientError as e:
        print(f"❌ Error fetching logs: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Fetch SageMaker training job logs')
    parser.add_argument('--job-name', required=True, help='Training job name')
    parser.add_argument('--region', default='us-east-2', help='AWS region')
    parser.add_argument('--limit', type=int, default=200, help='Number of log lines to fetch')
    parser.add_argument('--all-streams', action='store_true', help='Fetch from all log streams')
    args = parser.parse_args()
    
    log_group = '/aws/sagemaker/TrainingJobs'
    
    print("=" * 80)
    print(f"Fetching logs for: {args.job_name}")
    print("=" * 80)
    print(f"Log Group: {log_group}")
    print(f"Region: {args.region}\n")
    
    # Get log streams
    streams = get_log_streams(log_group, args.job_name, args.region)
    
    if not streams:
        print("❌ No log streams found")
        print("\nPossible reasons:")
        print("  1. Job hasn't started yet")
        print("  2. Job name is incorrect")
        print("  3. Logs have been deleted or expired")
        return
    
    print(f"Found {len(streams)} log stream(s):\n")
    
    for i, stream in enumerate(streams, 1):
        stream_name = stream['logStreamName']
        print(f"  {i}. {stream_name}")
    
    print("\n" + "=" * 80)
    
    # Fetch logs from the most recent stream (or all if requested)
    streams_to_fetch = streams if args.all_streams else [streams[0]]
    
    for stream in streams_to_fetch:
        stream_name = stream['logStreamName']
        print(f"\nLogs from: {stream_name}")
        print("=" * 80)
        
        events = fetch_logs(log_group, stream_name, args.region, args.limit)
        
        if not events:
            print("  (No log events)")
            continue
        
        for event in events:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            message = event['message'].rstrip()
            print(f"[{timestamp.strftime('%H:%M:%S')}] {message}")
    
    print("\n" + "=" * 80)
    print(f"Total log entries fetched: {sum(len(fetch_logs(log_group, s['logStreamName'], args.region, args.limit)) for s in streams_to_fetch)}")

if __name__ == '__main__':
    main()

