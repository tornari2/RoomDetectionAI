#!/bin/bash
# Build and push Docker container for SageMaker training
# Handles platform-specific builds for Apple Silicon Macs

set -e

REGION="us-east-2"
ACCOUNT_ID="971422717446"
REPOSITORY="room-detection-yolov8"
IMAGE_TAG="latest"

echo "=========================================="
echo "Building and Pushing Docker Container"
echo "=========================================="
echo "Repository: $REPOSITORY"
echo "Region: $REGION"
echo ""

# Authenticate to AWS public ECR (for base PyTorch image)
echo "1. Authenticating to AWS public ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.us-east-1.amazonaws.com

# Authenticate to your ECR
echo "2. Authenticating to your ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Detect platform
PLATFORM="linux/amd64"
if [[ $(uname -m) == "arm64" ]]; then
    echo "3. Detected Apple Silicon Mac - using platform linux/amd64 for SageMaker compatibility"
else
    echo "3. Building for native platform"
fi

# Build container
echo "4. Building Docker container (this may take 15-30 minutes)..."
docker build --platform $PLATFORM -t $REPOSITORY:$IMAGE_TAG sagemaker/

# Tag for ECR
echo "5. Tagging image for ECR..."
docker tag $REPOSITORY:$IMAGE_TAG $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY:$IMAGE_TAG

# Push to ECR
echo "6. Pushing to ECR (this may take a few minutes)..."
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY:$IMAGE_TAG

echo ""
echo "=========================================="
echo "✅ Container built and pushed successfully!"
echo "=========================================="
echo ""
echo "Image URI: $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY:$IMAGE_TAG"
echo ""
echo "Next step: Launch training job"
echo "  python3 sagemaker/scripts/run_training.py --role <your-role-arn>"

