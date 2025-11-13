# AWS AI/ML Services Documentation

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
11. [Troubleshooting & Security](#troubleshooting--security)

---

## Architecture Overview

```
┌─────────────┐
│   User      │
│  (Browser)  │
└─────┬───────┘
      │ HTTPS
      ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (REST API)                   │
│  • /upload    POST   - Upload blueprint                      │
│  • /status    GET    - Check processing status               │
│  • /process   POST   - Trigger room detection                │
└─────┬───────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS Lambda (Python 3.11)                        │
│  Handler: room-detection-ai-handler-dev                      │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │ Upload        │  │ Processing    │  │ Status         │  │
│  │ Handler       │  │ Handler       │  │ Handler        │  │
│  └───────┬───────┘  └───────┬───────┘  └────────┬───────┘  │
└──────────┼──────────────────┼──────────────────┼───────────┘
           │                  │                  │
           ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────────┐   ┌──────────────┐
    │ Amazon   │      │  SageMaker   │   │  DynamoDB    │
    │    S3    │      │  Endpoint    │   │   Status     │
    │ Blueprints│     │ (YOLOv8n)   │   │   Table      │
    └──────────┘      └──────────────┘   └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ CloudWatch   │
                      │  Logs &      │
                      │  Metrics     │
                      └──────────────┘
```

---

## Amazon SageMaker

### 1. Training Job Configuration

**Purpose**: Train YOLOv8n model on custom blueprint dataset

**Instance Configuration**:
```yaml
Instance Type: ml.g4dn.xlarge
vCPU: 4
Memory: 16 GB
GPU: NVIDIA T4 (16 GB VRAM)
Storage: 100 GB EBS volume
Cost: $0.736/hour
```

**Training Container**:
- **Base Image**: Custom Docker image with PyTorch 2.0.1
- **Framework**: Ultralytics YOLOv8
- **ECR Repository**: `971422717446.dkr.ecr.us-east-2.amazonaws.com/room-detection-yolov8:latest`

**Dockerfile (Training)**:
```dockerfile
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

# Install dependencies
RUN pip install --no-cache-dir \
    ultralytics==8.0.120 \
    opencv-python-headless \
    Pillow \
    pyyaml \
    tqdm

# Copy training script
COPY train.py /opt/ml/code/train.py
ENV SAGEMAKER_PROGRAM train.py

WORKDIR /opt/ml
```

**Hyperparameters**:
```json
{
  "epochs": 300,
  "batch_size": 16,
  "img_size": 640,
  "model_size": "yolov8n.pt",
  "lr0": 0.01,
  "lrf": 0.01,
  "cos_lr": true,
  "warmup_epochs": 3,
  "optimizer": "SGD",
  "momentum": 0.937,
  "weight_decay": 0.0005,
  "box": 7.5,
  "cls": 0.5,
  "dfl": 1.5,
  "patience": 50,
  "single_cls": true,
  "pretrained": true
}
```

**Input Data Channels**:
```python
{
  "training": "s3://room-detection-ai-blueprints-dev-971422717446/training/",
  "validation": "s3://room-detection-ai-blueprints-dev-971422717446/training/validation/"
}
```

**Output Artifacts**:
- **Location**: `s3://room-detection-ai-blueprints-dev-971422717446/models/`
- **Files**:
  - `best.pt` - Best model checkpoint (by validation mAP)
  - `last.pt` - Final epoch checkpoint
  - `metrics.json` - Training metrics
  - `confusion_matrix.png` - Validation confusion matrix

**IAM Role Requirements**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::room-detection-ai-blueprints-dev-971422717446/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/sagemaker/*"
    }
  ]
}
```

---

### 2. Inference Endpoint Configuration

**Purpose**: Real-time room detection inference

**Instance Configuration**:
```yaml
Endpoint Name: room-detection-yolov8-endpoint
Instance Type: ml.c5.xlarge
vCPU: 4
Memory: 8 GB
Storage: Root volume only (no GPU needed)
Cost: $0.204/hour
Autoscaling: 1-3 instances (target: 70% CPU utilization)
```

**Model Configuration**:
```yaml
Model Name: room-detection-yolov8-model-v1
Model Data: s3://room-detection-ai-blueprints-dev-971422717446/models/best.pt
Container: 971422717446.dkr.ecr.us-east-2.amazonaws.com/room-detection-yolov8-inference:latest
Environment Variables:
  MODEL_PATH: /opt/ml/model/best.pt
  CONFIDENCE_THRESHOLD: 0.25
  IOU_THRESHOLD: 0.45
```

**Inference Container**:
```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install --no-cache-dir \
    torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu \
    ultralytics==8.0.120 \
    opencv-python-headless \
    Pillow \
    flask

# Copy inference script
COPY inference.py /opt/ml/code/inference.py

WORKDIR /opt/ml
EXPOSE 8080

CMD ["python", "/opt/ml/code/inference.py"]
```

**Inference Script (`inference.py`)**:
```python
from ultralytics import YOLO
import json
import base64
from io import BytesIO
from PIL import Image

model = YOLO('/opt/ml/model/best.pt')

def model_fn(model_dir):
    """Load model"""
    return YOLO(f'{model_dir}/best.pt')

def input_fn(request_body, content_type):
    """Deserialize input"""
    if content_type == 'application/json':
        data = json.loads(request_body)
        image_data = base64.b64decode(data['image'])
        return Image.open(BytesIO(image_data))
    raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_data, model):
    """Run inference"""
    results = model(input_data, conf=0.25, iou=0.45)
    return results[0]

def output_fn(prediction, accept):
    """Serialize output"""
    boxes = prediction.boxes.xyxyn.cpu().numpy()  # Normalized coords
    confidences = prediction.boxes.conf.cpu().numpy()
    
    rooms = []
    for i, box in enumerate(boxes):
        rooms.append({
            'id': f'room_{i+1}',
            'bounding_box': [
                int(box[0] * 1000),
                int(box[1] * 1000),
                int(box[2] * 1000),
                int(box[3] * 1000)
            ],
            'confidence': float(confidences[i])
        })
    
    return json.dumps({'rooms': rooms})
```

**Endpoint Autoscaling Policy**:
```json
{
  "TargetTrackingScalingPolicyConfiguration": {
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  },
  "MinCapacity": 1,
  "MaxCapacity": 3
}
```

---

## AWS Lambda

### 1. Function Configuration

**Function Name**: `room-detection-ai-handler-dev`

**Runtime Configuration**:
```yaml
Runtime: Python 3.11
Architecture: x86_64
Memory: 512 MB
Timeout: 60 seconds
Ephemeral Storage: 512 MB
Environment Variables:
  S3_BUCKET: room-detection-ai-blueprints-dev-971422717446
  DYNAMODB_TABLE: room-detection-status-dev
  SAGEMAKER_ENDPOINT: room-detection-yolov8-endpoint
  AWS_REGION: us-east-2
```

**Layers**:
- **Klayers Pillow**: `arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p311-Pillow:3`
- **Klayers NumPy**: `arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p311-numpy:7`

**Code Structure**:
```
lambda/
├── handler.py              # Main Lambda handler
├── requirements.txt        # Dependencies
└── utils/
    ├── __init__.py
    ├── status_manager.py   # DynamoDB interactions
    ├── image_processor.py  # Image preprocessing
    └── async_processor.py  # SageMaker invocation
```

---

### 2. Handler Functions

#### **Upload Handler**

**Route**: `POST /upload`

**Functionality**:
1. Validate incoming image (format, size)
2. Generate unique blueprint ID
3. Upload image to S3
4. Create status record in DynamoDB
5. Return blueprint ID and upload confirmation

**Code**:
```python
def handle_upload(event):
    """Handle blueprint upload"""
    # Parse request
    body = json.loads(event['body'])
    image_data = base64.b64decode(body['image'])
    
    # Validate image
    try:
        img = Image.open(BytesIO(image_data))
        if img.size[0] > 5000 or img.size[1] > 5000:
            return error_response(400, "Image too large")
    except Exception as e:
        return error_response(400, f"Invalid image: {str(e)}")
    
    # Generate ID and upload to S3
    blueprint_id = str(uuid.uuid4())
    s3_key = f"blueprints/{blueprint_id}.png"
    
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=image_data,
        ContentType='image/png'
    )
    
    # Create status record
    status_manager.create_status(
        blueprint_id=blueprint_id,
        status='uploaded',
        s3_key=s3_key
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'blueprint_id': blueprint_id,
            'message': 'Upload successful'
        })
    }
```

---

#### **Processing Handler**

**Route**: `POST /process`

**Functionality**:
1. Retrieve image from S3
2. Preprocess image (resize, normalize)
3. Invoke SageMaker endpoint
4. Parse detection results
5. Update DynamoDB with results
6. Generate name hints for rooms

**Code**:
```python
def handle_processing(event):
    """Handle room detection processing"""
    body = json.loads(event['body'])
    blueprint_id = body['blueprint_id']
    
    # Update status to processing
    status_manager.update_status(
        blueprint_id=blueprint_id,
        status='processing'
    )
    
    # Get image from S3
    status = status_manager.get_status(blueprint_id)
    image_data = s3_client.get_object(
        Bucket=S3_BUCKET,
        Key=status['s3_key']
    )['Body'].read()
    
    # Invoke SageMaker
    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType='application/json',
            Body=json.dumps({
                'image': base64.b64encode(image_data).decode('utf-8')
            })
        )
        
        result = json.loads(response['Body'].read())
        rooms = result['rooms']
        
        # Generate name hints
        for room in rooms:
            room['name_hint'] = generate_name_hint(room['bounding_box'])
        
        # Update status with results
        status_manager.update_status(
            blueprint_id=blueprint_id,
            status='completed',
            detected_rooms=rooms
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'blueprint_id': blueprint_id,
                'detected_rooms': rooms
            })
        }
        
    except Exception as e:
        status_manager.update_status(
            blueprint_id=blueprint_id,
            status='failed',
            error=str(e)
        )
        return error_response(500, f"Processing failed: {str(e)}")
```

---

#### **Status Handler**

**Route**: `GET /status?blueprint_id=<id>`

**Functionality**:
1. Query DynamoDB for blueprint status
2. Return status and detected rooms (if completed)

**Code**:
```python
def handle_status(event):
    """Get processing status"""
    blueprint_id = event['queryStringParameters']['blueprint_id']
    
    status = status_manager.get_status(blueprint_id)
    
    if not status:
        return error_response(404, "Blueprint not found")
    
    return {
        'statusCode': 200,
        'body': json.dumps(status, default=decimal_to_float)
    }
```

---

### 3. IAM Role & Permissions

**Role Name**: `RoomDetectionLambdaRole`

**Managed Policies**:
- `AWSLambdaBasicExecutionRole` (CloudWatch Logs)

**Inline Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::room-detection-ai-blueprints-dev-971422717446/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-2:971422717446:table/room-detection-status-dev"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:InvokeEndpoint"
      ],
      "Resource": "arn:aws:sagemaker:us-east-2:971422717446:endpoint/room-detection-yolov8-endpoint"
    }
  ]
}
```

---

## Amazon S3

### Bucket Configuration

**Bucket Name**: `room-detection-ai-blueprints-dev-971422717446`

**Region**: `us-east-2` (Ohio)

**Folder Structure**:
```
room-detection-ai-blueprints-dev-971422717446/
├── blueprints/              # User-uploaded blueprints
│   ├── <uuid>.png
│   └── ...
├── training/                # Training dataset
│   ├── images/
│   │   └── train/
│   │       └── *.png
│   └── labels/
│       └── train/
│           └── *.txt
├── validation/              # Validation dataset
│   ├── images/
│   │   └── val/
│   └── labels/
│       └── val/
└── models/                  # Trained model artifacts
    ├── best.pt
    └── last.pt
```

**Bucket Policies**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::room-detection-ai-blueprints-dev-971422717446/*"
    }
  ]
}
```

**CORS Configuration**:
```json
[
  {
    "AllowedOrigins": ["https://your-frontend-domain.com"],
    "AllowedMethods": ["GET", "POST", "PUT"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

**Lifecycle Policy**:
```json
{
  "Rules": [
    {
      "Id": "DeleteOldBlueprints",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "blueprints/"
      },
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

---

## Amazon DynamoDB

### Table Configuration

**Table Name**: `room-detection-status-dev`

**Primary Key**:
- **Partition Key**: `blueprint_id` (String)

**Attributes**:
```python
{
  "blueprint_id": "string",       # Unique blueprint identifier
  "status": "string",             # uploaded | processing | completed | failed
  "s3_key": "string",             # S3 object key
  "detected_rooms": "list",       # List of room objects (if completed)
  "error": "string",              # Error message (if failed)
  "created_at": "number",         # Timestamp (Unix epoch)
  "updated_at": "number",         # Timestamp (Unix epoch)
  "ttl": "number"                 # TTL for automatic deletion (30 days)
}
```

**Provisioned Capacity**:
```yaml
Read Capacity Units: 5 RCU (auto-scaling enabled)
Write Capacity Units: 5 WCU (auto-scaling enabled)
```

**Auto-Scaling Configuration**:
```json
{
  "ReadCapacityUnits": {
    "MinimumUnits": 5,
    "MaximumUnits": 100,
    "TargetValue": 70.0
  },
  "WriteCapacityUnits": {
    "MinimumUnits": 5,
    "MaximumUnits": 100,
    "TargetValue": 70.0
  }
}
```

**TTL Configuration**:
- **TTL Attribute**: `ttl`
- **Expiration**: 30 days after creation
- **Purpose**: Automatic cleanup of old records

**Global Secondary Indexes**: None (simple query pattern by blueprint_id)

---

## API Gateway

### REST API Configuration

**API Name**: `room-detection-api-dev`

**Endpoint Type**: Regional

**Routes**:

1. **POST /upload**
   - **Integration**: Lambda proxy integration
   - **Authorization**: None (public)
   - **Request Validation**: Enabled (schema-based)
   - **Request Body Schema**:
     ```json
     {
       "type": "object",
       "properties": {
         "image": {
           "type": "string",
           "description": "Base64-encoded image"
         }
       },
       "required": ["image"]
     }
     ```

2. **POST /process**
   - **Integration**: Lambda proxy integration
   - **Authorization**: None (public)
   - **Request Body Schema**:
     ```json
     {
       "type": "object",
       "properties": {
         "blueprint_id": {
           "type": "string",
           "description": "UUID from upload"
         }
       },
       "required": ["blueprint_id"]
     }
     ```

3. **GET /status**
   - **Integration**: Lambda proxy integration
   - **Authorization**: None (public)
   - **Query Parameters**: `blueprint_id` (required)

**CORS Configuration**:
```yaml
Access-Control-Allow-Origin: '*'
Access-Control-Allow-Methods: 'GET,POST,OPTIONS'
Access-Control-Allow-Headers: 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
```

**Rate Limiting (Usage Plan)**:
```yaml
Throttle:
  Rate Limit: 100 requests/second
  Burst Limit: 200 requests
Quota: 10,000 requests/day
```

**Deployment Stage**:
- **Stage Name**: `prod`
- **Stage Variables**: None
- **CloudWatch Logging**: Enabled (INFO level)
- **X-Ray Tracing**: Disabled (optional for debugging)

---

## IAM Roles & Permissions

### Summary of IAM Roles

| Service | Role Name | Purpose |
|---------|-----------|---------|
| SageMaker Training | `SageMakerTrainingRole` | Access S3 for datasets, ECR for containers |
| SageMaker Inference | `SageMakerInferenceRole` | Invoke endpoint, log to CloudWatch |
| Lambda | `RoomDetectionLambdaRole` | S3, DynamoDB, SageMaker endpoint access |
| API Gateway | `ApiGatewayInvokeRole` | Invoke Lambda functions |

*(Detailed policies provided in respective sections above)*

---

## CloudWatch Monitoring

### Metrics & Alarms

**Lambda Metrics**:
- **Invocations**: Total requests processed
- **Errors**: Failed invocations (target < 1%)
- **Duration**: Average execution time (target < 5s)
- **Throttles**: Rate-limited requests (alarm if > 0)

**SageMaker Metrics**:
- **ModelLatency**: Inference time (P50, P95, P99)
- **Invocations**: Endpoint invocations per minute
- **ModelInvocation4XXErrors**: Client errors (target < 1%)
- **ModelInvocation5XXErrors**: Server errors (target < 0.1%)
- **CPUUtilization**: Instance CPU usage (target 40-70%)

**DynamoDB Metrics**:
- **ConsumedReadCapacityUnits**: Read throughput
- **ConsumedWriteCapacityUnits**: Write throughput
- **UserErrors**: Client errors (4xx)
- **SystemErrors**: Service errors (5xx)

**CloudWatch Alarms**:
```yaml
- HighErrorRate:
    Metric: Lambda Errors
    Threshold: > 5 errors in 5 minutes
    Action: Send SNS notification

- HighLatency:
    Metric: SageMaker ModelLatency (P95)
    Threshold: > 500ms
    Action: Scale out endpoint

- LowEndpointHealth:
    Metric: SageMaker ModelInvocation5XXErrors
    Threshold: > 3 errors in 1 minute
    Action: Send SNS notification
```

**Log Groups**:
- `/aws/lambda/room-detection-ai-handler-dev`
- `/aws/sagemaker/TrainingJobs`
- `/aws/sagemaker/Endpoints/room-detection-yolov8-endpoint`
- `/aws/apigateway/room-detection-api-dev`

**Log Retention**: 7 days (configurable)

---

## Cost Analysis

### Monthly Cost Breakdown (Estimated)

**Assumptions**:
- 10,000 API requests/month
- Average processing time: 5 seconds/request
- Endpoint runs 24/7 with 1 instance

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **SageMaker Endpoint** | ml.c5.xlarge (1 instance, 24/7) | $147.00 |
| **Lambda** | 512 MB, 10K invocations @ 5s each | $0.42 |
| **API Gateway** | 10K requests | $0.035 |
| **S3** | 50 GB storage + 10K requests | $1.15 |
| **DynamoDB** | 5 RCU/WCU provisioned | $2.85 |
| **CloudWatch** | Logs (1 GB/month) | $0.50 |
| **Data Transfer** | Minimal (within region) | $0.50 |
| **TOTAL** | | **~$152.50/month** |

**Cost Optimization Strategies**:
1. **Autoscaling**: Scale down endpoint during low-traffic hours (save ~30%)
2. **Reserved Instances**: 1-year commitment for SageMaker (save ~20%)
3. **Lambda-only inference**: Remove SageMaker endpoint, run inference in Lambda (save $147/month, but slower)

---

## Deployment Guide

### 1. Prerequisites
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Install Docker
# (for building custom containers)
```

### 2. Deploy Training Infrastructure
```bash
# Build training container
cd sagemaker/
docker build -t room-detection-training -f Dockerfile .

# Tag and push to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 971422717446.dkr.ecr.us-east-2.amazonaws.com
docker tag room-detection-training:latest 971422717446.dkr.ecr.us-east-2.amazonaws.com/room-detection-yolov8:latest
docker push 971422717446.dkr.ecr.us-east-2.amazonaws.com/room-detection-yolov8:latest

# Start training job
aws sagemaker create-training-job --cli-input-json file://training-job-config.json
```

### 3. Deploy Inference Endpoint
```bash
# Build inference container
docker build -t room-detection-inference -f Dockerfile.inference .
docker tag room-detection-inference:latest 971422717446.dkr.ecr.us-east-2.amazonaws.com/room-detection-yolov8-inference:latest
docker push 971422717446.dkr.ecr.us-east-2.amazonaws.com/room-detection-yolov8-inference:latest

# Create model
aws sagemaker create-model --model-name room-detection-yolov8-model-v1 --cli-input-json file://model-config.json

# Create endpoint config
aws sagemaker create-endpoint-config --endpoint-config-name room-detection-config --cli-input-json file://endpoint-config.json

# Create endpoint
aws sagemaker create-endpoint --endpoint-name room-detection-yolov8-endpoint --endpoint-config-name room-detection-config
```

### 4. Deploy Lambda Function
```bash
cd lambda/
pip install -r requirements.txt -t .
zip -r lambda_deployment.zip .
aws lambda update-function-code --function-name room-detection-ai-handler-dev --zip-file fileb://lambda_deployment.zip
```

### 5. Deploy API Gateway
```bash
# Use CloudFormation template
aws cloudformation deploy \
  --template-file aws/infrastructure/cloudformation.yaml \
  --stack-name room-detection-api-stack \
  --capabilities CAPABILITY_IAM
```

---

## Troubleshooting & Security

### Common Issues

**1. SageMaker Endpoint Timeout**
- **Symptom**: Lambda returns 504 Gateway Timeout
- **Cause**: Inference taking > 60 seconds
- **Fix**: Increase Lambda timeout to 120s, optimize model inference

**2. Out of Memory (Lambda)**
- **Symptom**: Lambda crashes with "Runtime exited with error: signal: killed"
- **Cause**: Image processing exceeds 512 MB memory
- **Fix**: Increase Lambda memory to 1024 MB or resize images before processing

**3. DynamoDB Throttling**
- **Symptom**: `ProvisionedThroughputExceededException`
- **Cause**: Read/write capacity exceeded
- **Fix**: Enable auto-scaling or increase provisioned capacity

**4. S3 Access Denied**
- **Symptom**: `AccessDenied` error when uploading/downloading
- **Cause**: Missing IAM permissions or bucket policy
- **Fix**: Verify Lambda role has `s3:GetObject` and `s3:PutObject` permissions

### Security Best Practices

1. **API Gateway**:
   - Enable API keys for production
   - Implement AWS WAF for DDoS protection
   - Use Amazon Cognito for user authentication

2. **Lambda**:
   - Store secrets in AWS Secrets Manager (not environment variables)
   - Enable VPC integration for private SageMaker endpoints
   - Use least-privilege IAM roles

3. **S3**:
   - Enable bucket encryption (SSE-S3 or SSE-KMS)
   - Block public access (unless intentional)
   - Enable versioning for blueprints

4. **DynamoDB**:
   - Enable point-in-time recovery (PITR)
   - Encrypt data at rest (AWS-managed keys)

5. **SageMaker**:
   - Use VPC for endpoint isolation
   - Enable data encryption in transit (HTTPS only)
   - Rotate IAM credentials regularly

---

## Conclusion

This AWS AI/ML infrastructure provides a scalable, cost-effective solution for room detection in architectural blueprints. The architecture leverages:
- **SageMaker** for model training and real-time inference
- **Lambda** for serverless backend logic
- **S3 + DynamoDB** for data storage and status tracking
- **API Gateway** for RESTful API

**Key Strengths**:
- **Autoscaling**: Handles traffic spikes automatically
- **Pay-per-use**: No upfront costs, scales to zero
- **Managed services**: Minimal operational overhead

**Future Enhancements**:
- AWS Batch for large-scale batch processing
- Amazon Rekognition Custom Labels as alternative to SageMaker
- AWS Step Functions for complex workflow orchestration

---

**Document Version**: 1.0  
**Last Updated**: November 10, 2024  
**AWS Account ID**: 971422717446  
**Region**: us-east-2 (Ohio)

