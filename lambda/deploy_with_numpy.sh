#!/bin/bash
# Deploy Lambda with bundled numpy (no layers)

set -e

echo "Creating deployment package with bundled dependencies..."

# Create temp directory
TMP_DIR=$(mktemp -d)
echo "Working in: $TMP_DIR"

# Copy handler and utils
cp handler.py "$TMP_DIR/"
cp -r utils "$TMP_DIR/"

# Install dependencies directly into package
cd "$TMP_DIR"
pip install numpy pillow --target . --platform manylinux2014_x86_64 --python-version 3.11 --only-binary=:all: --upgrade --no-deps

# Remove unnecessary files to reduce size
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true  
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Create zip
zip -r9 deployment.zip . -x "*.pyc" -x "*__pycache__/*"

echo ""
echo "Package size: $(du -h deployment.zip | cut -f1)"
echo ""

# Remove layers from Lambda function first
echo "Removing problematic layers..."
aws lambda update-function-configuration \
    --function-name room-detection-ai-handler-dev \
    --layers 

sleep 5

# Deploy
echo "Deploying to Lambda..."
aws lambda update-function-code \
    --function-name room-detection-ai-handler-dev \
    --zip-file fileb://deployment.zip \
    --publish

# Cleanup
cd -
rm -rf "$TMP_DIR"

echo ""
echo "✅ Deployment complete with bundled numpy!"

