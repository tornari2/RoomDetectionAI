# Room Detection AI

AI-powered room detection system for architectural blueprints using YOLOv8 and AWS infrastructure.

## Overview

This project provides an end-to-end solution for detecting rooms in architectural blueprint images. It uses a YOLOv8 model trained on blueprint datasets, deployed on AWS SageMaker, with a serverless API and React frontend.

## Features

- **AI-Powered Detection**: YOLOv8 model trained on 4,200+ blueprint images
- **Serverless Architecture**: AWS Lambda + API Gateway for scalable processing
- **Async Processing**: Non-blocking API with status polling
- **Modern Frontend**: React + TypeScript with drag-and-drop file upload
- **Export Functionality**: Download annotated images and JSON coordinates

## Architecture

- **Backend**: AWS Lambda (Python) for image processing
- **ML Model**: YOLOv8 deployed on SageMaker Serverless Inference
- **Storage**: S3 for blueprint storage
- **API**: API Gateway REST API
- **Frontend**: React + TypeScript single-page application

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
│       └── lambda-config.json     # Lambda configuration
├── lambda/
│   ├── handler.py                 # Lambda entry point
│   ├── utils/                     # Utility modules
│   └── tests/                     # Lambda tests
├── sagemaker/
│   ├── Dockerfile                 # Custom container
│   ├── train.py                  # Training script
│   └── config/                   # Training configuration
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── services/             # API client
│   │   └── utils/                # Utility functions
│   └── package.json
└── README.md
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

