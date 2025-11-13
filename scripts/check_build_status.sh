#!/bin/bash
# Quick build status checker

BUILD_ID=$(aws codebuild list-builds-for-project \
    --project-name room-detection-docker-build \
    --region us-east-2 \
    --max-items 1 \
    --query 'ids[0]' \
    --output text)

if [ -z "$BUILD_ID" ] || [ "$BUILD_ID" = "None" ]; then
    echo "No active build found"
    exit 1
fi

STATUS=$(aws codebuild batch-get-builds \
    --ids "$BUILD_ID" \
    --region us-east-2 \
    --query 'builds[0].buildStatus' \
    --output text 2>/dev/null)

PHASE=$(aws codebuild batch-get-builds \
    --ids "$BUILD_ID" \
    --region us-east-2 \
    --query 'builds[0].currentPhase' \
    --output text 2>/dev/null)

echo "Status: $STATUS"
echo "Phase: $PHASE"
echo ""
echo "Build ID: $BUILD_ID"
echo "Console: https://console.aws.amazon.com/codesuite/codebuild/projects/room-detection-docker-build/build/$BUILD_ID"

if [ "$STATUS" = "SUCCEEDED" ]; then
    echo ""
    echo "✅ Build completed! Run: ./scripts/check_build_and_deploy.sh"
elif [ "$STATUS" = "FAILED" ]; then
    echo ""
    echo "❌ Build failed - check console link above"
elif [ "$STATUS" = "IN_PROGRESS" ]; then
    echo ""
    echo "⏳ Still building (this is normal - takes 8-12 minutes)"
    echo "   Running on AWS CodeBuild, NOT your Mac"
fi

