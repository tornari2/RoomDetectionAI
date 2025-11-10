#!/usr/bin/env python3
"""
Get the LATEST SageMaker logs to see why worker is dying
"""

import boto3
from datetime import datetime, timedelta

client = boto3.client('logs', region_name='us-east-2')
log_group = '/aws/sagemaker/Endpoints/room-detection-yolov8-endpoint'

print("Fetching LATEST logs from new EC2 endpoint...")
print("=" * 80)

try:
    # Get most recent log streams
    streams = client.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=5
    )
    
    if not streams['logStreams']:
        print("No log streams found")
        exit(1)
    
    # Get events from the NEWEST stream (last 10 minutes)
    stream_name = streams['logStreams'][0]['logStreamName']
    print(f"Latest stream: {stream_name}\n")
    
    start_time = int((datetime.now() - timedelta(minutes=10)).timestamp() * 1000)
    
    events = client.get_log_events(
        logGroupName=log_group,
        logStreamName=stream_name,
        startTime=start_time,
        startFromHead=False,
        limit=100
    )
    
    print("RECENT ERROR LOGS:\n")
    
    # Filter for errors and warnings
    error_keywords = ['ERROR', 'WARN', 'Exception', 'Traceback', 'died', 'failed', 'crash']
    
    for event in events['events'][-50:]:
        message = event['message'].strip()
        
        # Show all errors/warnings
        if any(keyword in message for keyword in error_keywords):
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            print(f"[{timestamp.strftime('%H:%M:%S')}] {message}")
    
    print("\n" + "=" * 80)
    print("\nALL RECENT LOGS (last 30):\n")
    
    for event in events['events'][-30:]:
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
        message = event['message'].strip()
        print(f"[{timestamp.strftime('%H:%M:%S')}] {message}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

