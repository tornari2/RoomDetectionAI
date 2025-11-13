#!/usr/bin/env python3
"""
Get recent SageMaker endpoint logs
"""

import boto3
from datetime import datetime, timedelta

client = boto3.client('logs', region_name='us-east-2')

log_group = '/aws/sagemaker/Endpoints/room-detection-yolov8-endpoint'

print(f"Fetching recent logs from: {log_group}")
print("=" * 80)

try:
    # Get log streams (most recent first)
    streams = client.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=3
    )
    
    if not streams['logStreams']:
        print("No log streams found")
        exit(1)
    
    # Get the most recent stream
    stream_name = streams['logStreams'][0]['logStreamName']
    print(f"Latest log stream: {stream_name}\n")
    
    # Get recent log events (last 30 minutes)
    start_time = int((datetime.now() - timedelta(minutes=30)).timestamp() * 1000)
    
    events = client.get_log_events(
        logGroupName=log_group,
        logStreamName=stream_name,
        startTime=start_time,
        startFromHead=False,
        limit=50
    )
    
    print("Recent logs:\n")
    for event in events['events'][-20:]:  # Last 20 events
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
        message = event['message'].strip()
        print(f"[{timestamp.strftime('%H:%M:%S')}] {message}")
    
except client.exceptions.ResourceNotFoundException:
    print(f"\n❌ Log group not found: {log_group}")
    print("The endpoint might not have logged anything yet.")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 80)

