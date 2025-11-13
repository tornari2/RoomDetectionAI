#!/bin/bash
# Script to check CodeBuild status and update SageMaker endpoint when ready

set -e

PROJECT_NAME="room-detection-docker-build"
REGION="us-east-2"
ENDPOINT_NAME="room-detection-yolov8-endpoint"

echo "=========================================="
echo "CodeBuild Status Check & Endpoint Update"
echo "=========================================="
echo ""

# Get latest build ID
BUILD_ID=$(aws codebuild list-builds-for-project \
    --project-name "$PROJECT_NAME" \
    --region "$REGION" \
    --max-items 1 \
    --query 'ids[0]' \
    --output text)

if [ -z "$BUILD_ID" ] || [ "$BUILD_ID" = "None" ]; then
    echo "❌ No build found. Start a build first:"
    echo "   ./scripts/build_with_codebuild.sh"
    exit 1
fi

echo "Build ID: $BUILD_ID"
echo ""

# Check build status
STATUS=$(aws codebuild batch-get-builds \
    --ids "$BUILD_ID" \
    --region "$REGION" \
    --query 'builds[0].buildStatus' \
    --output text 2>/dev/null)

PHASE=$(aws codebuild batch-get-builds \
    --ids "$BUILD_ID" \
    --region "$REGION" \
    --query 'builds[0].currentPhase' \
    --output text 2>/dev/null)

echo "Status: $STATUS"
echo "Phase: $PHASE"
echo ""

if [ "$STATUS" = "SUCCEEDED" ]; then
    echo "✅ Build completed successfully!"
    echo ""
    echo "Updating SageMaker endpoint..."
    echo ""
    
    # Delete old endpoint
    echo "Deleting old endpoint..."
    aws sagemaker delete-endpoint \
        --endpoint-name "$ENDPOINT_NAME" \
        --region "$REGION" 2>&1 | grep -v "does not exist" || true
    
    echo "Waiting 30 seconds for endpoint deletion..."
    sleep 30
    
    # Deploy new endpoint
    echo "Deploying new endpoint..."
    python3 sagemaker/scripts/deploy_model.py
    
    echo ""
    echo "✅ Endpoint update complete!"
    echo ""
    echo "Test the endpoint:"
    echo "  python3 sagemaker/tests/test_inference.py --endpoint-name $ENDPOINT_NAME --image-path <path-to-image>"
    
elif [ "$STATUS" = "FAILED" ]; then
    echo "❌ Build failed!"
    echo ""
    echo "View logs:"
    LOG_LINK=$(aws codebuild batch-get-builds \
        --ids "$BUILD_ID" \
        --region "$REGION" \
        --query 'builds[0].logs.deepLink' \
        --output text 2>/dev/null)
    echo "  $LOG_LINK"
    exit 1
    
elif [ "$STATUS" = "IN_PROGRESS" ]; then
    echo "⏳ Build still in progress..."
    echo ""
    echo "Monitor build:"
    echo "  aws codebuild batch-get-builds --ids $BUILD_ID --region $REGION"
    echo ""
    echo "Or check AWS Console:"
    echo "  https://console.aws.amazon.com/codesuite/codebuild/projects/$PROJECT_NAME/build/$BUILD_ID"
    echo ""
    echo "Run this script again when build completes:"
    echo "  ./scripts/check_build_and_deploy.sh"
    
else
    echo "⚠️  Unknown status: $STATUS"
    exit 1
fi

