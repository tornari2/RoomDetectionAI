# Testing Lambda Function

## Quick Start

### Option 1: Test on AWS Lambda (Recommended)

This tests the actual deployed Lambda function:

```bash
# Using the test script
python3 lambda/tests/test_lambda.py --aws

# Or using AWS CLI directly
aws lambda invoke \
  --function-name room-detection-processor \
  --region us-east-2 \
  --payload file://lambda/tests/test_event.json \
  response.json

cat response.json | python3 -m json.tool
```

### Option 2: Test Locally

This runs the Lambda handler code locally (requires AWS credentials and S3 access):

```bash
python3 lambda/tests/test_lambda.py --local
```

## Prerequisites

### 1. Upload a Test Image to S3

Before testing, you need to upload a test blueprint image to S3:

```bash
# Upload a test image
aws s3 cp <path-to-your-blueprint-image> \
  s3://room-detection-ai-blueprints-dev/test/blueprint_sample.png \
  --region us-east-2

# Or use any existing blueprint image
aws s3 cp s3://room-detection-ai-blueprints-dev/training/data/images/<some-image>.png \
  s3://room-detection-ai-blueprints-dev/test/blueprint_sample.png \
  --region us-east-2
```

### 2. Update Test Event

Edit `lambda/tests/test_event.json` to point to your test image:

```json
{
  "blueprint_id": "bp_test_001",
  "s3_bucket": "room-detection-ai-blueprints-dev",
  "s3_key": "test/blueprint_sample.png"
}
```

## Test Event Structure

The Lambda function expects an event with:
- `blueprint_id`: Unique identifier for the blueprint
- `s3_bucket`: S3 bucket name (optional, defaults to env var)
- `s3_key`: S3 object key (path to the image)

## Expected Response

### Success Response:
```json
{
  "statusCode": 200,
  "body": {
    "blueprint_id": "bp_test_001",
    "status": "completed",
    "processing_time_ms": 15420,
    "detected_rooms": [
      {
        "id": "room_001",
        "bounding_box": [50, 50, 200, 300],
        "confidence": 0.95
      }
    ]
  }
}
```

### Error Response:
```json
{
  "statusCode": 400,
  "body": {
    "blueprint_id": "bp_test_001",
    "status": "failed",
    "error": "missing_s3_key",
    "message": "s3_key is required"
  }
}
```

## Troubleshooting

### Error: "Failed to download image from S3"
- Check that the S3 key exists: `aws s3 ls s3://room-detection-ai-blueprints-dev/test/`
- Verify Lambda IAM role has S3 GetObject permission
- Check the S3 bucket name matches the environment variable

### Error: "Failed to invoke SageMaker endpoint"
- Verify the SageMaker endpoint is InService: 
  ```bash
  aws sagemaker describe-endpoint --endpoint-name room-detection-yolov8-endpoint --region us-east-2
  ```
- Check Lambda IAM role has SageMaker InvokeEndpoint permission

### Error: "Function not found"
- Verify function name: `aws lambda list-functions --region us-east-2 | grep room-detection`
- Check you're using the correct region

## Testing with Different Images

Create multiple test events for different scenarios:

```bash
# Test event 1: Small blueprint
echo '{"blueprint_id":"bp_small","s3_bucket":"room-detection-ai-blueprints-dev","s3_key":"test/small.png"}' > test_event_small.json

# Test event 2: Large blueprint
echo '{"blueprint_id":"bp_large","s3_bucket":"room-detection-ai-blueprints-dev","s3_key":"test/large.png"}' > test_event_large.json

# Test with different events
python3 lambda/tests/test_lambda.py --aws --event-file test_event_small.json
```

