#!/bin/bash
# Rebuild and push Docker image with inference script

set -e

echo "=========================================="
echo "Rebuilding Docker Image for Inference"
echo "=========================================="

# Configuration
REGION="us-east-2"
ECR_REGISTRY="971422717446.dkr.ecr.us-east-2.amazonaws.com"
REPOSITORY="room-detection-yolov8"
IMAGE_TAG="latest"
IMAGE_URI="${ECR_REGISTRY}/${REPOSITORY}:${IMAGE_TAG}"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SAGEMAKER_DIR="$(dirname "$SCRIPT_DIR")"

echo "Region: $REGION"
echo "Image URI: $IMAGE_URI"
echo "SageMaker directory: $SAGEMAKER_DIR"
echo ""

# Login to ECR (both private and public)
echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Login to AWS Public ECR for base images
echo "Logging in to AWS Public ECR..."
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws

# Login to SageMaker base image ECR
echo "Logging in to SageMaker base image ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.us-east-1.amazonaws.com

# Build Docker image with platform specification (linux/amd64 for SageMaker)
# Disable buildkit to use legacy builder and avoid OCI manifest issues
echo ""
echo "Building Docker image..."
cd "$SAGEMAKER_DIR"

# Use legacy Docker builder (no buildx) to avoid OCI manifest issues
DOCKER_BUILDKIT=0 docker build --platform linux/amd64 -t ${REPOSITORY}:${IMAGE_TAG} .

# Tag image
echo ""
echo "Tagging image..."
docker tag ${REPOSITORY}:${IMAGE_TAG} ${IMAGE_URI}

# Push image
echo ""
echo "Pushing image to ECR..."
docker push ${IMAGE_URI}

echo ""
echo "=========================================="
echo "✅ Docker image rebuilt and pushed!"
echo "=========================================="
echo "Image URI: $IMAGE_URI"
echo ""
echo "You can now deploy the model with:"
echo "  python3 sagemaker/scripts/deploy_model.py"

