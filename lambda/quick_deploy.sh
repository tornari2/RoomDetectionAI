#!/bin/bash
# Quick deployment script to update Lambda handler

echo "================================================"
echo "Updating Lambda function handler..."
echo "================================================"

cd "$(dirname "$0")"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure'"
    exit 1
fi

# Get the Lambda function name
FUNCTION_NAME="${1:-room-detection-ai-handler-dev}"

echo "Function name: $FUNCTION_NAME"

# Create a temporary deployment package
echo "Creating deployment package..."
TMP_DIR=$(mktemp -d)
cp handler.py "$TMP_DIR/"
cp -r utils "$TMP_DIR/" 2>/dev/null || true

# Create zip file
cd "$TMP_DIR"
zip -q -r lambda_update.zip .
cd - >/dev/null

echo "Uploading to Lambda..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://$TMP_DIR/lambda_update.zip" \
    --publish

if [ $? -eq 0 ]; then
    echo "✓ Successfully updated Lambda function!"
    echo ""
    echo "Next steps:"
    echo "1. Try uploading a photo again"
    echo "2. Check CloudWatch Logs for the function to see debug output"
    echo "3. If it still fails, run the test script locally first:"
    echo "   python lambda/test_upload_local.py path/to/your/photo.png"
else
    echo "❌ Failed to update Lambda function"
    exit 1
fi

# Cleanup
rm -rf "$TMP_DIR"

