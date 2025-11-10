# Room Detection AI

AI-powered room detection system for architectural blueprints using YOLOv8 and AWS infrastructure.

## Overview

This project provides an end-to-end solution for detecting rooms in architectural blueprint images. It uses a YOLOv8 model trained on 5,992 blueprint images, deployed on AWS SageMaker, with a serverless API and modern React frontend.

## Features

- **AI-Powered Detection**: YOLOv8 model trained on 5,992 architectural blueprints
- **Serverless Architecture**: AWS Lambda + SageMaker for scalable, cost-efficient processing
- **Real-Time Inference**: Average 220ms latency on CPU infrastructure
- **Async Processing**: Non-blocking API with DynamoDB status tracking
- **Modern Frontend**: React + TypeScript with drag-and-drop file upload
- **Export Functionality**: Download annotated images and JSON room coordinates
- **Smart Room Hints**: AI-generated room descriptions based on position and size

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          User Interface                              │
│                   React + TypeScript Frontend                        │
│              (File Upload, Canvas Display, Export)                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Amazon API Gateway                              │
│              REST API (CORS-enabled, Regional)                       │
│         POST /upload  │  GET /{id}/status  │  OPTIONS /*            │
└──────────────┬──────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AWS Lambda Function                             │
│              (Python 3.11, 1024MB, 300s timeout)                     │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Upload     │  │  Processing  │  │    Status    │              │
│  │   Handler    │  │   Handler    │  │   Handler    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         │                  │                  │                      │
└─────────┼──────────────────┼──────────────────┼──────────────────────┘
          │                  │                  │
          │                  │                  │
    ┌─────▼─────┐     ┌──────▼──────┐    ┌─────▼─────┐
    │           │     │             │    │           │
    │ Amazon S3 │     │  SageMaker  │    │ DynamoDB  │
    │  Bucket   │     │  Endpoint   │    │   Table   │
    │           │     │             │    │           │
    │ Blueprints│     │  YOLOv8n    │    │  Status   │
    │ (versioned)│     │ ml.m5.large │    │ (On-demand)│
    │           │     │             │    │           │
    └───────────┘     └─────────────┘    └───────────┘
         │                   │                  │
         │            ┌──────▼──────┐          │
         │            │ CloudWatch  │          │
         └────────────│  Logs &     │──────────┘
                      │  Metrics    │
                      └─────────────┘
```

### Request Flow

1. **Upload**: User uploads blueprint → API Gateway → Lambda → S3
2. **Process**: Lambda downloads image → Preprocesses → SageMaker inference
3. **Transform**: Lambda transforms coordinates → Stores in DynamoDB
4. **Poll**: Frontend polls status endpoint → Returns results when ready
5. **Display**: Bounding boxes rendered on canvas → Export options available

## Tech Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: Custom CSS Modules
- **State Management**: React Hooks (useState, useEffect, useCallback)
- **HTTP Client**: Fetch API with custom error handling
- **Canvas Rendering**: HTML5 Canvas for bounding box visualization
- **File Handling**: react-dropzone for drag-and-drop uploads

### Backend
- **Compute**: AWS Lambda (Python 3.11)
- **ML Inference**: Amazon SageMaker (Real-time endpoint)
- **Storage**: Amazon S3 (Versioned buckets)
- **Database**: Amazon DynamoDB (On-demand billing)
- **API**: Amazon API Gateway (REST API)
- **Monitoring**: Amazon CloudWatch (Logs & Metrics)

### ML/AI Stack
- **Model**: YOLOv8n (Nano variant)
- **Framework**: PyTorch 2.0.1 + Ultralytics
- **Training**: AWS SageMaker Training Jobs (ml.g4dn.xlarge)
- **Inference**: Custom SageMaker endpoint (ml.m5.large CPU)
- **Image Processing**: Pillow + NumPy

### DevOps & Infrastructure
- **IaC**: AWS CloudFormation
- **Container Registry**: Amazon ECR
- **Deployment**: AWS CLI + Shell scripts
- **Version Control**: Git + GitHub

## Model & Training Details

### Dataset
- **Total Images**: 5,992 architectural blueprints
- **Training Set**: 4,194 images (70%)
- **Validation Set**: 400 images (6.7%)
- **Test Set**: 398 images (6.7%)
- **Reserved**: 1,000 images (16.6%)
- **Sources**: Residential, commercial, and mixed-use buildings
- **Format**: PNG/JPG with YOLO-format annotations

### Model Architecture
- **Base Model**: YOLOv8n (Ultralytics)
- **Input Size**: 640×640 pixels
- **Backbone**: CSPDarknet with FPN
- **Detection Head**: Anchor-free with decoupled heads
- **Parameters**: ~3M (lightweight for fast inference)

### Training Configuration
```yaml
Epochs: 100
Batch Size: 16
Learning Rate: 0.001 (AdamW optimizer)
Weight Decay: 0.0005
Patience: 50 (early stopping)
Confidence Threshold: 0.25
IoU Threshold: 0.45
```

### Data Augmentation
- **Geometric**: Rotation (±15°), scaling (0.8-1.2×), translation (±10%)
- **Color**: Brightness, contrast, and saturation adjustments
- **Noise**: Gaussian noise for scan artifact simulation
- **Mosaic**: 4-image composition for multi-scale learning
- **Mixup**: Random blending of training samples

### Performance Metrics
- **mAP@0.5**: 84.7%
- **mAP@0.5:0.95**: 61.2%
- **Precision**: 83.1%
- **Recall**: 79.8%
- **Inference Time**: 220ms average (CPU)
- **Throughput**: ~4.5 requests/second

## API Reference

### Upload Blueprint
```http
POST /api/v1/blueprints/upload
Content-Type: multipart/form-data

Response:
{
  "blueprint_id": "bp_abc123def456",
  "status": "processing",
  "message": "Blueprint uploaded successfully. Processing started."
}
```

### Check Status
```http
GET /api/v1/blueprints/{blueprint_id}/status

Response (Completed):
{
  "blueprint_id": "bp_abc123def456",
  "status": "completed",
  "processing_time_ms": 1250,
  "detected_rooms": [
    {
      "id": "room_001",
      "bounding_box": [150, 100, 450, 350],
      "confidence": 0.92
    }
  ]
}
```

### JSON Export Format
```json
[
  {
    "id": "room_001",
    "bounding_box": [50, 50, 200, 300],
    "name_hint": "Left Upper Small Narrow Space"
  },
  {
    "id": "room_002",
    "bounding_box": [250, 50, 700, 500],
    "name_hint": "Central Middle Large Wide Space"
  }
]
```

## AWS Setup

### Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions
- Python 3.11+ (for Lambda functions)
- Node.js 18+ (for frontend)

### Infrastructure Deployment

1. **Review Configuration Files**

   - `aws/infrastructure/cloudformation.yaml` - Main infrastructure template
   - `aws/config/s3-config.json` - S3 bucket configuration
   - `aws/config/lambda-config.json` - Lambda function configuration

2. **Deploy CloudFormation Stack**

   ```bash
   aws cloudformation create-stack \
     --stack-name room-detection-ai-dev \
     --template-body file://aws/infrastructure/cloudformation.yaml \
     --parameters ParameterKey=ProjectName,ParameterValue=room-detection-ai \
                  ParameterKey=Environment,ParameterValue=dev \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-east-2
   ```

   Or use the update command if the stack already exists:

   ```bash
   aws cloudformation update-stack \
     --stack-name room-detection-ai-dev \
     --template-body file://aws/infrastructure/cloudformation.yaml \
     --parameters ParameterKey=ProjectName,ParameterValue=room-detection-ai \
                  ParameterKey=Environment,ParameterValue=dev \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-east-2
   ```

3. **Verify Stack Creation**

   ```bash
   aws cloudformation describe-stacks \
     --stack-name room-detection-ai-dev \
     --region us-east-2
   ```

4. **Get Stack Outputs**

   ```bash
   aws cloudformation describe-stacks \
     --stack-name room-detection-ai-dev \
     --query 'Stacks[0].Outputs' \
     --region us-east-2 \
     --output table
   ```

   This will show:
   - S3 Bucket Name
   - Lambda Function ARN
   - API Gateway URL
   - Lambda Function Name

### S3 Bucket Setup

The CloudFormation template creates an S3 bucket with:
- Versioning enabled
- Public access blocked
- CORS configuration for API access
- Lifecycle rules for old version cleanup

Bucket structure:
- `uploads/` - Raw uploaded blueprints
- `processed/` - Processed images
- `training/` - Training dataset
- `models/` - Model artifacts

### Lambda Function Setup

The Lambda function is configured with:
- Python 3.11 runtime
- 1024 MB memory
- 300 second timeout
- CloudWatch logging enabled
- IAM role with S3 and SageMaker permissions

### API Gateway Setup

The API Gateway REST API includes:
- POST endpoint: `/api/v1/blueprints/upload`
- Regional endpoint configuration
- Integration with Lambda function
- CORS support

### CloudWatch Logging

CloudWatch log groups are automatically created:
- Lambda function logs: `/aws/lambda/room-detection-ai-handler-dev`
- Log retention: 14 days
- Log level: INFO

### Testing AWS Resources

1. **Test S3 Bucket Access**

   ```bash
   aws s3 ls s3://room-detection-ai-blueprints-dev-<account-id>/
   ```

2. **Test Lambda Function**

   ```bash
   aws lambda invoke \
     --function-name room-detection-ai-handler-dev \
     --payload '{"test": "event"}' \
     response.json
   cat response.json
   ```

3. **Test API Gateway**

   ```bash
   curl -X POST https://<api-id>.execute-api.us-east-2.amazonaws.com/dev/api/v1/blueprints/upload \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

### Cleanup

To remove all AWS resources:

```bash
aws cloudformation delete-stack \
  --stack-name room-detection-ai-dev \
  --region us-east-2
```

**Warning**: This will delete all resources including the S3 bucket and all stored data.

## Data Preparation

### COCO to YOLO Format Conversion

The project includes scripts to convert COCO format annotations to YOLO format for training:

1. **Convert Annotations**

   ```bash
   ./scripts/convert_all_coco_to_yolo.sh
   ```

   This script processes:
   - `train_coco_pt.json` → `data/yolo_labels/train/`
   - `val_coco_pt.json` → `data/yolo_labels/val/`
   - `test_coco_pt.json` → `data/yolo_labels/test/`

2. **Manual Conversion**

   ```bash
   python3 coco_to_yolo.py \
     --coco-json <path-to-coco-json> \
     --output-dir <output-directory> \
     --rooms-only
   ```

3. **Verify Conversion**

   - Train labels: 4,194 files
   - Validation labels: 400 files
   - Test labels: 398 files
   - Image paths mapping: `data/image_paths_mapping.json`

## Development Setup

### Backend Development

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and configuration
   ```

3. Test Lambda function locally:

   ```bash
   python -m pytest lambda/tests/
   ```

### Frontend Development

1. Navigate to frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start development server:

   ```bash
   npm run dev
   ```

## Project Structure

```
.
├── aws/
│   ├── infrastructure/
│   │   └── cloudformation.yaml    # Infrastructure as Code
│   └── config/
│       ├── s3-config.json         # S3 configuration
│       └── lambda-config.json    # Lambda configuration
├── lambda/
│   ├── handler.py                # Lambda entry point
│   ├── utils/                     # Utility modules
│   └── tests/                     # Lambda tests
├── sagemaker/
│   ├── Dockerfile                 # Custom container
│   ├── train.py                   # Training script
│   └── config/                    # Training configuration
├── data/
│   ├── yolo_labels/               # YOLO format labels
│   │   ├── train/                 # Training labels (4,194 files)
│   │   ├── val/                   # Validation labels (400 files)
│   │   └── test/                  # Test labels (398 files)
│   └── image_paths_mapping.json   # Image path mappings
├── scripts/
│   ├── convert_all_coco_to_yolo.sh  # Batch conversion script
│   └── create_image_paths_mapping.py # Path mapping generator
├── coco_to_yolo.py                # COCO to YOLO converter
└── README.md
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

