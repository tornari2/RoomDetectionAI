# AWS AI/ML Services Documentation
## Room Detection AI System

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Amazon SageMaker](#amazon-sagemaker)
3. [AWS Lambda](#aws-lambda)
4. [Amazon S3](#amazon-s3)
5. [Amazon DynamoDB](#amazon-dynamodb)
6. [API Gateway](#api-gateway)
7. [IAM Roles & Permissions](#iam-roles--permissions)
8. [CloudWatch Monitoring](#cloudwatch-monitoring)
9. [Cost Analysis](#cost-analysis)
10. [Deployment Guide](#deployment-guide)

---

## Architecture Overview

### High-Level Architecture
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │─────▶│  API Gateway │─────▶│   Lambda    │
│  Frontend   │◀─────│              │◀─────│  Function   │
└─────────────┘      └──────────────┘      └──────┬──────┘
                                                   │
                     ┌─────────────────────────────┼───────────────┐
                     │                             │               │
                     ▼                             ▼               ▼
              ┌─────────────┐              ┌─────────────┐  ┌──────────┐
              │  SageMaker  │              │   Amazon    │  │ DynamoDB │
              │  Endpoint   │              │     S3      │  │  Table   │
              └─────────────┘              └─────────────┘  └──────────┘
```

### Service Components
| Service | Purpose | Configuration |
|---------|---------|---------------|
| SageMaker | Model training & inference | YOLOv8 on ml.m5.large |
| Lambda | Request processing | Python 3.11, 1024MB memory |
| S3 | Blueprint storage | Versioned, CORS-enabled |
| DynamoDB | Status tracking | On-demand billing, 7-day TTL |
| API Gateway | REST API | Regional, CORS-enabled |
| CloudWatch | Monitoring & logging | 7-day retention |

---

## Amazon SageMaker

### Overview
Amazon SageMaker is used for both training the YOLOv8 model and hosting it as a real-time inference endpoint.

### 1. SageMaker Training Job

#### Training Configuration
```yaml
TrainingJobName: room-detection-yolov8-training-{timestamp}
RoleArn: arn:aws:iam::{account}:role/SageMakerExecutionRole
AlgorithmSpecification:
  TrainingImage: {account}.dkr.ecr.{region}.amazonaws.com/room-detection:latest
  TrainingInputMode: File
InputDataConfig:
  - ChannelName: training
    DataSource:
      S3DataSource:
        S3DataType: S3Prefix
        S3Uri: s3://room-detection-training-{timestamp}/train/
        S3DataDistributionType: FullyReplicated
  - ChannelName: validation
    DataSource:
      S3DataSource:
        S3DataType: S3Prefix
        S3Uri: s3://room-detection-training-{timestamp}/val/
        S3DataDistributionType: FullyReplicated
OutputDataConfig:
  S3OutputPath: s3://room-detection-training-{timestamp}/output/
ResourceConfig:
  InstanceType: ml.g4dn.xlarge
  InstanceCount: 1
  VolumeSizeInGB: 30
StoppingCondition:
  MaxRuntimeInSeconds: 86400  # 24 hours
```

#### Training Instance Details
- **Instance Type**: `ml.g4dn.xlarge`
- **vCPUs**: 4
- **Memory**: 16 GB
- **GPU**: 1x NVIDIA T4 (16 GB GPU memory)
- **Cost**: ~$0.526/hour
- **Typical Training Time**: 3-4 hours

#### Hyperparameters
```json
{
  "epochs": "100",
  "batch_size": "16",
  "img_size": "640",
  "learning_rate": "0.001",
  "weight_decay": "0.0005",
  "optimizer": "AdamW",
  "patience": "50",
  "conf_threshold": "0.25",
  "iou_threshold": "0.45"
}
```

#### Training Docker Container
```dockerfile
FROM pytorch/pytorch:2.0.1-cuda11.8-cudnn8-runtime

# Install dependencies
RUN pip install ultralytics==8.0.196 \
    opencv-python-headless==4.8.1.78 \
    pillow==10.0.1 \
    numpy==1.24.3 \
    pyyaml==6.0.1

# Copy training script
COPY train.py /opt/ml/code/train.py

# Set entrypoint
ENV SAGEMAKER_PROGRAM train.py
```

### 2. SageMaker Endpoint

#### Endpoint Configuration
```yaml
EndpointName: room-detection-yolov8-endpoint
EndpointConfigName: room-detection-yolov8-config-{timestamp}
ProductionVariants:
  - VariantName: AllTraffic
    ModelName: room-detection-yolov8-model
    InitialInstanceCount: 1
    InstanceType: ml.m5.large
    InitialVariantWeight: 1.0
DataCaptureConfig:
  EnableCapture: false
```

#### Endpoint Instance Details
- **Instance Type**: `ml.m5.large`
- **vCPUs**: 2
- **Memory**: 8 GB
- **Network**: Up to 10 Gbps
- **Cost**: ~$0.115/hour
- **Average Inference Time**: 220ms

#### Model Configuration
```python
# model.tar.gz structure
model.tar.gz/
├── code/
│   ├── inference.py          # Custom inference handler
│   └── requirements.txt      # Python dependencies
├── best.pt                   # Trained YOLOv8 weights
└── model_config.json         # Model metadata
```

#### Inference Handler (inference.py)
```python
import json
import base64
import io
import torch
from PIL import Image
from ultralytics import YOLO

def model_fn(model_dir):
    """Load the model"""
    model_path = f"{model_dir}/best.pt"
    model = YOLO(model_path)
    return model

def input_fn(request_body, content_type):
    """Preprocess input data"""
    if content_type == 'application/json':
        data = json.loads(request_body)
        image_bytes = base64.b64decode(data['image'])
        image = Image.open(io.BytesIO(image_bytes))
        return image
    raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_data, model):
    """Run inference"""
    results = model(input_data, conf=0.25, iou=0.45)
    return results

def output_fn(prediction, accept):
    """Format output"""
    if accept == 'application/json':
        boxes = prediction[0].boxes
        detected_rooms = []
        
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            
            detected_rooms.append({
                'id': f'room_{i+1:03d}',
                'bounding_box': [
                    int(x1 * 1000 / 640),  # Normalize to 0-1000
                    int(y1 * 1000 / 640),
                    int(x2 * 1000 / 640),
                    int(y2 * 1000 / 640)
                ],
                'confidence': conf
            })
        
        return json.dumps({
            'detected_rooms': detected_rooms,
            'processing_time_ms': int(prediction[0].speed['inference'])
        })
    raise ValueError(f"Unsupported accept type: {accept}")
```

#### Endpoint Auto-Scaling (Optional)
```yaml
AutoScalingPolicies:
  - PolicyName: TargetTrackingScaling
    PolicyType: TargetTrackingScaling
    TargetTrackingScalingPolicyConfiguration:
      TargetValue: 70.0
      PredefinedMetricSpecification:
        PredefinedMetricType: SageMakerVariantInvocationsPerInstance
      ScaleInCooldown: 300
      ScaleOutCooldown: 60
```

---

## AWS Lambda

### Lambda Function Configuration

#### Function Specifications
```yaml
FunctionName: room-detection-ai-handler-dev
Runtime: python3.11
Handler: handler.lambda_handler
MemorySize: 1024  # MB
Timeout: 300      # seconds
Environment:
  Variables:
    SAGEMAKER_ENDPOINT_NAME: room-detection-yolov8-endpoint
    S3_BUCKET: room-detection-ai-blueprints-dev-{account}
    STATUS_TABLE_NAME: room-detection-status-dev
    FORCE_UPDATE: "{timestamp}"
Layers:
  - arn:aws:lambda:{region}:770693421928:layer:Klayers-p311-Pillow:7
  - arn:aws:lambda:{region}:770693421928:layer:Klayers-p311-numpy:12
```

#### Lambda Layers
**1. Pillow Layer** (Image Processing)
- **ARN**: `arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p311-Pillow:7`
- **Size**: ~4.9 MB
- **Purpose**: Image loading, resizing, format conversion

**2. NumPy Layer** (Numerical Operations)
- **ARN**: `arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p311-numpy:12`
- **Size**: ~20 MB
- **Purpose**: Array operations, coordinate transformations

#### Function Code Structure
```
lambda/
├── handler.py                    # Main Lambda handler
├── utils/
│   ├── __init__.py
│   ├── image_processor.py        # Image preprocessing
│   ├── coordinate_transformer.py # Coordinate conversion
│   └── status_manager.py         # DynamoDB operations
├── requirements.txt              # Python dependencies
└── tests/
    ├── test_handler.py
    └── test_lambda.py
```

#### Key Dependencies (requirements.txt)
```txt
boto3==1.34.10
Pillow==10.0.1
numpy==1.24.3
```

#### Handler Functions

**1. Upload Handler** (`handle_upload`)
```python
def handle_upload(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process API Gateway upload request
    - Parse multipart form data
    - Validate file (type, size, signature)
    - Upload to S3
    - Create DynamoDB status entry
    - Trigger async processing
    """
```

**2. Processing Handler** (`handle_processing`)
```python
def handle_processing(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process blueprint asynchronously
    - Download from S3
    - Preprocess image (resize to 640x640)
    - Invoke SageMaker endpoint
    - Transform coordinates to original size
    - Update DynamoDB with results
    """
```

**3. Status Handler** (`handle_status`)
```python
def handle_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check processing status
    - Query DynamoDB by blueprint_id
    - Return status: processing/completed/failed
    - Include results if completed
    """
```

#### Concurrency Settings
```yaml
ReservedConcurrentExecutions: 10  # Limit to 10 concurrent executions
ProvisionedConcurrency: 0         # No provisioned concurrency (cold starts acceptable)
```

#### Dead Letter Queue (Optional)
```yaml
DeadLetterConfig:
  TargetArn: arn:aws:sqs:{region}:{account}:room-detection-dlq
```

---

## Amazon S3

### Bucket Configuration

#### Bucket Name
```
room-detection-ai-blueprints-dev-{account}
```

#### Versioning
```yaml
VersioningConfiguration:
  Status: Enabled
```

#### Lifecycle Policy
```yaml
Rules:
  - Id: DeleteOldVersions
    Status: Enabled
    NoncurrentVersionExpirationInDays: 30
  - Id: DeleteOldUploads
    Status: Enabled
    Prefix: uploads/
    ExpirationInDays: 7
```

#### CORS Configuration
```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000,
      "ExposeHeaders": ["ETag"]
    }
  ]
}
```

#### Bucket Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowLambdaAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::room-detection-ai-blueprints-dev-*/*"
    },
    {
      "Sid": "DenyInsecureConnections",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::room-detection-ai-blueprints-dev-*",
        "arn:aws:s3:::room-detection-ai-blueprints-dev-*/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

#### Object Structure
```
s3://room-detection-ai-blueprints-dev-{account}/
├── uploads/
│   └── {blueprint_id}/
│       └── blueprint.{png|jpg}
├── processed/
│   └── {blueprint_id}/
│       └── annotated.png
└── models/
    └── yolov8-room-detection/
        └── model.tar.gz
```

---

## Amazon DynamoDB

### Table Configuration

#### Table Name
```
room-detection-status-dev
```

#### Schema
```yaml
TableName: room-detection-status-dev
AttributeDefinitions:
  - AttributeName: blueprint_id
    AttributeType: S
KeySchema:
  - AttributeName: blueprint_id
    KeyType: HASH
BillingMode: PAY_PER_REQUEST  # On-demand pricing
```

#### Time-To-Live (TTL)
```yaml
TimeToLiveSpecification:
  Enabled: true
  AttributeName: ttl
```

#### Item Structure
```json
{
  "blueprint_id": "bp_abc123def456",
  "status": "completed",
  "message": "Processing completed successfully",
  "created_at": "2025-11-10T12:00:00.000Z",
  "updated_at": "2025-11-10T12:00:15.000Z",
  "processing_time_ms": 1250,
  "detected_rooms": [
    {
      "id": "room_001",
      "bounding_box": [150, 100, 450, 350],
      "confidence": 0.92
    }
  ],
  "ttl": 1731244800
}
```

#### Status Values
- `processing`: Blueprint is being analyzed
- `completed`: Analysis finished successfully
- `failed`: Error during processing

#### Global Secondary Indexes (Optional)
```yaml
GlobalSecondaryIndexes:
  - IndexName: status-index
    KeySchema:
      - AttributeName: status
        KeyType: HASH
      - AttributeName: created_at
        KeyType: RANGE
    Projection:
      ProjectionType: ALL
    ProvisionedThroughput:
      ReadCapacityUnits: 5
      WriteCapacityUnits: 5
```

#### Point-in-Time Recovery
```yaml
PointInTimeRecoverySpecification:
  PointInTimeRecoveryEnabled: true
```

---

## API Gateway

### REST API Configuration

#### API Details
```yaml
ApiName: room-detection-api-dev
Description: API for Room Detection AI blueprint processing
ProtocolType: REST
EndpointType: REGIONAL
```

#### API Resources & Methods

**1. Upload Endpoint**
```
POST /api/v1/blueprints/upload
```
- **Integration**: Lambda Proxy
- **Content Type**: `multipart/form-data`
- **Max Request Size**: 50MB
- **Response Codes**: 200, 400, 413, 500

**2. Status Endpoint**
```
GET /api/v1/blueprints/{blueprint_id}/status
```
- **Integration**: Lambda Proxy
- **Path Parameter**: `blueprint_id`
- **Response Codes**: 200, 404, 500

**3. OPTIONS (CORS Preflight)**
```
OPTIONS /api/v1/blueprints/upload
OPTIONS /api/v1/blueprints/{blueprint_id}/status
```

#### CORS Configuration
```yaml
CorsConfiguration:
  AllowOrigins:
    - '*'
  AllowMethods:
    - GET
    - POST
    - OPTIONS
  AllowHeaders:
    - Content-Type
    - X-Amz-Date
    - Authorization
    - X-Api-Key
  MaxAge: 3000
```

#### Request Validation
```json
{
  "validateRequestBody": true,
  "validateRequestParameters": true
}
```

#### Throttling Settings
```yaml
ThrottleSettings:
  RateLimit: 100      # requests per second
  BurstLimit: 200     # concurrent requests
```

#### API Stages
```yaml
Stages:
  - StageName: dev
    Description: Development environment
    Variables:
      environment: dev
    MethodSettings:
      - ResourcePath: '/*'
        HttpMethod: '*'
        LoggingLevel: INFO
        DataTraceEnabled: true
        MetricsEnabled: true
```

#### Custom Domain (Optional)
```yaml
DomainName: api.roomdetection.example.com
CertificateArn: arn:aws:acm:{region}:{account}:certificate/{id}
EndpointType: REGIONAL
BasePath: 'v1'
```

---

## IAM Roles & Permissions

### 1. Lambda Execution Role

#### Role Name
```
room-detection-ai-lambda-role-dev
```

#### Trust Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### Attached Policies

**Managed Policy**: `AWSLambdaBasicExecutionRole`
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

**Custom Policy**: S3 Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::room-detection-ai-blueprints-dev-*/*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::room-detection-ai-blueprints-dev-*"
    }
  ]
}
```

**Custom Policy**: SageMaker Invoke
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sagemaker:InvokeEndpoint",
      "Resource": "arn:aws:sagemaker:*:*:endpoint/room-detection-yolov8-endpoint"
    }
  ]
}
```

**Custom Policy**: DynamoDB Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/room-detection-status-dev"
    }
  ]
}
```

**Custom Policy**: Lambda Self-Invocation
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:*:*:function:room-detection-ai-handler-dev"
    }
  ]
}
```

### 2. SageMaker Execution Role

#### Role Name
```
SageMakerExecutionRole
```

#### Trust Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### Attached Policies

**Managed Policy**: `AmazonSageMakerFullAccess`

**Custom Policy**: S3 Model Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::room-detection-training-*",
        "arn:aws:s3:::room-detection-training-*/*"
      ]
    }
  ]
}
```

**Custom Policy**: ECR Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## CloudWatch Monitoring

### Log Groups

#### Lambda Function Logs
```
/aws/lambda/room-detection-ai-handler-dev
```
- **Retention**: 7 days
- **Size**: ~50-100 MB/day
- **Log Level**: INFO

#### SageMaker Endpoint Logs
```
/aws/sagemaker/Endpoints/room-detection-yolov8-endpoint
```
- **Retention**: 7 days
- **Includes**: Invocation logs, model errors

#### API Gateway Logs
```
API-Gateway-Execution-Logs_{api-id}/dev
```
- **Retention**: 7 days
- **Log Format**: CLF (Common Log Format)

### CloudWatch Metrics

#### Lambda Metrics
- `Invocations`: Total function invocations
- `Errors`: Number of errors
- `Duration`: Execution time (ms)
- `Throttles`: Throttled requests
- `ConcurrentExecutions`: Concurrent invocations

#### SageMaker Metrics
- `ModelInvocations`: Endpoint invocations
- `ModelLatency`: Inference latency (μs)
- `Invocation4XXErrors`: Client errors
- `Invocation5XXErrors`: Server errors
- `CPUUtilization`: CPU usage (%)
- `MemoryUtilization`: Memory usage (%)

#### DynamoDB Metrics
- `ConsumedReadCapacityUnits`: Read capacity consumed
- `ConsumedWriteCapacityUnits`: Write capacity consumed
- `UserErrors`: Request errors
- `SystemErrors`: DynamoDB errors

### CloudWatch Alarms

```yaml
Alarms:
  - AlarmName: LambdaHighErrorRate
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold
    
  - AlarmName: SageMakerHighLatency
    MetricName: ModelLatency
    Namespace: AWS/SageMaker
    Statistic: Average
    Period: 300
    EvaluationPeriods: 2
    Threshold: 500000  # 500ms in microseconds
    ComparisonOperator: GreaterThanThreshold
```

---

## Cost Analysis

### Monthly Cost Breakdown (Estimated)

#### SageMaker Endpoint
```
Instance: ml.m5.large
Hours per month: 730
Cost: 730 × $0.115 = $84/month
```

#### Lambda
```
Requests: 10,000/month
Average duration: 2s
Memory: 1024 MB

Compute cost: 10,000 × 2s × (1024/1024) × $0.0000166667 = $0.33
Request cost: 10,000 × $0.0000002 = $0.002
Total: ~$0.35/month
```

#### DynamoDB
```
On-demand pricing
Writes: 10,000/month × $1.25/million = $0.0125
Reads: 30,000/month × $0.25/million = $0.0075
Storage: 1 GB × $0.25/GB = $0.25
Total: ~$0.27/month
```

#### S3
```
Storage: 10 GB × $0.023/GB = $0.23
PUT requests: 10,000 × $0.005/1000 = $0.05
GET requests: 30,000 × $0.0004/1000 = $0.012
Total: ~$0.29/month
```

#### API Gateway
```
Requests: 10,000/month
Cost: 10,000 × $0.0000035 = $0.035
Total: ~$0.04/month
```

#### **Total Monthly Cost: ~$85/month**

### Cost Optimization Recommendations
1. **Use Serverless Inference** for low-traffic scenarios
2. **Implement Auto-Scaling** for SageMaker endpoints
3. **Enable S3 Intelligent-Tiering** for older blueprints
4. **Use CloudWatch Logs Insights** instead of exporting all logs
5. **Implement caching** in API Gateway for status checks

---

## Deployment Guide

### Prerequisites
- AWS CLI configured with appropriate credentials
- Docker installed (for container builds)
- Python 3.11+ installed
- Node.js 18+ (for frontend)

### Step 1: Deploy Infrastructure
```bash
# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file aws/infrastructure/cloudformation.yaml \
  --stack-name room-detection-ai-dev \
  --parameter-overrides \
    ProjectName=room-detection-ai \
    Environment=dev \
  --capabilities CAPABILITY_NAMED_IAM
```

### Step 2: Build and Push Docker Image
```bash
# Build training container
cd sagemaker
docker build -t room-detection:latest -f Dockerfile .

# Tag and push to ECR
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin {account}.dkr.ecr.us-east-2.amazonaws.com

docker tag room-detection:latest \
  {account}.dkr.ecr.us-east-2.amazonaws.com/room-detection:latest

docker push {account}.dkr.ecr.us-east-2.amazonaws.com/room-detection:latest
```

### Step 3: Upload Training Data
```bash
# Sync training data to S3
aws s3 sync data/yolo_labels s3://room-detection-training-{timestamp}/
```

### Step 4: Create Training Job
```bash
# Start SageMaker training job
python sagemaker/scripts/train_model.py \
  --training-image {account}.dkr.ecr.us-east-2.amazonaws.com/room-detection:latest \
  --data-path s3://room-detection-training-{timestamp}/ \
  --output-path s3://room-detection-training-{timestamp}/output/
```

### Step 5: Deploy Model to Endpoint
```bash
# Create SageMaker endpoint
python sagemaker/scripts/deploy_endpoint.py \
  --model-data s3://room-detection-training-{timestamp}/output/model.tar.gz \
  --endpoint-name room-detection-yolov8-endpoint \
  --instance-type ml.m5.large
```

### Step 6: Deploy Lambda Function
```bash
# Package and deploy Lambda
cd lambda
zip -r lambda_deployment.zip . -x "tests/*" -x "__pycache__/*"

aws lambda update-function-code \
  --function-name room-detection-ai-handler-dev \
  --zip-file fileb://lambda_deployment.zip
```

### Step 7: Deploy Frontend
```bash
# Build and deploy React frontend
cd frontend
npm install
npm run build

# Upload to S3 (if using S3 static hosting)
aws s3 sync dist/ s3://room-detection-frontend-dev/
```

### Step 8: Verify Deployment
```bash
# Test API endpoint
curl -X POST https://{api-id}.execute-api.us-east-2.amazonaws.com/dev/api/v1/blueprints/upload \
  -F "file=@test_blueprint.png"
```

---

## Troubleshooting

### Common Issues

#### 1. SageMaker Endpoint Not Responding
```bash
# Check endpoint status
aws sagemaker describe-endpoint \
  --endpoint-name room-detection-yolov8-endpoint

# Check CloudWatch logs
aws logs tail /aws/sagemaker/Endpoints/room-detection-yolov8-endpoint --follow
```

#### 2. Lambda Timeout Errors
- Increase timeout from 300s if needed
- Check SageMaker endpoint latency
- Verify network connectivity

#### 3. CORS Errors
- Verify API Gateway CORS configuration
- Check S3 bucket CORS settings
- Ensure proper headers in Lambda response

#### 4. DynamoDB Throttling
- Switch to on-demand billing mode
- Increase provisioned capacity if using provisioned mode
- Implement exponential backoff in Lambda

---

## Security Best Practices

1. **Enable VPC for Lambda** (if accessing private resources)
2. **Use AWS Secrets Manager** for sensitive configuration
3. **Enable encryption at rest** for S3 and DynamoDB
4. **Implement API rate limiting** in API Gateway
5. **Regular security audits** with AWS Inspector
6. **Enable CloudTrail** for audit logging
7. **Use least-privilege IAM policies**
8. **Enable MFA** for AWS account access

---

## Conclusion

This documentation provides comprehensive coverage of all AWS AI/ML services and configurations used in the Room Detection AI system. For updates or questions, refer to the main repository or contact the development team.

**Last Updated**: November 10, 2025  
**Version**: 1.0  
**Repository**: https://github.com/tornari2/RoomDetectionAI

