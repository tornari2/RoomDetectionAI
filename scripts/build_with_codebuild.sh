#!/bin/bash
# Simplified script to build Docker image using CodeBuild

set -e

PROJECT_NAME="room-detection-docker-build"
REGION="us-east-2"
BUCKET="room-detection-ai-blueprints-dev"
S3_KEY="codebuild/source.zip"

echo "=========================================="
echo "Build Docker Image with CodeBuild"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Step 1: Create source zip
echo ""
echo "Step 1: Creating source zip..."
cd "$PROJECT_ROOT"
zip -r /tmp/source.zip sagemaker/ buildspec.yml \
    -x '*.git*' '*.pyc' '__pycache__/*' '*.DS_Store' \
    -x 'sagemaker/outputs/*' 'sagemaker/logs/*' 'sagemaker/.sagemaker/*'

echo "✅ Source zip created: /tmp/source.zip"

# Step 2: Upload to S3
echo ""
echo "Step 2: Uploading to S3..."
aws s3 cp /tmp/source.zip "s3://${BUCKET}/${S3_KEY}" --region "$REGION"
echo "✅ Source uploaded to s3://${BUCKET}/${S3_KEY}"

# Step 3: Create CodeBuild project (if needed)
echo ""
echo "Step 3: Ensuring CodeBuild project exists..."
python3 "$SCRIPT_DIR/setup_codebuild.py" --create-project-only --region "$REGION" || true

# Step 4: Start build
echo ""
echo "Step 4: Starting CodeBuild build..."
BUILD_ID=$(aws codebuild start-build \
    --project-name "$PROJECT_NAME" \
    --region "$REGION" \
    --query 'build.id' \
    --output text)

echo "✅ Build started: $BUILD_ID"
echo ""
echo "Monitor build:"
echo "  aws codebuild batch-get-builds --ids $BUILD_ID --region $REGION"
echo ""
echo "AWS Console:"
echo "  https://console.aws.amazon.com/codesuite/codebuild/projects/$PROJECT_NAME/build/$BUILD_ID"
echo ""
echo "Once build completes, deploy with:"
echo "  python3 sagemaker/scripts/deploy_model.py"

