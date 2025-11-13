#!/bin/bash
# Create Lambda Layer with Pillow and numpy for Python 3.10

set -e

LAYER_NAME="room-detection-dependencies"
REGION="us-east-2"
PYTHON_VERSION="python3.10"

echo "Creating Lambda Layer with dependencies..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
LAYER_DIR="$TEMP_DIR/python"

mkdir -p "$LAYER_DIR"

echo "Installing Pillow and numpy for Linux (Python 3.10)..."

# Install dependencies for Linux
pip install \
    Pillow==10.0.0 \
    numpy==1.24.3 \
    -t "$LAYER_DIR" \
    --platform manylinux2014_x86_64 \
    --only-binary :all: \
    --python-version 310 \
    --no-deps \
    --upgrade

# Create zip file
cd "$TEMP_DIR"
zip -r layer.zip python/ > /dev/null

echo "✅ Layer package created: layer.zip"
echo "Size: $(du -h layer.zip | cut -f1)"

# Create Lambda Layer
echo ""
echo "Creating Lambda Layer: $LAYER_NAME"
LAYER_ARN=$(aws lambda publish-layer-version \
    --layer-name "$LAYER_NAME" \
    --description "Pillow and numpy for room detection Lambda" \
    --zip-file fileb://layer.zip \
    --compatible-runtimes "$PYTHON_VERSION" \
    --region "$REGION" \
    --query 'LayerVersionArn' \
    --output text)

echo "✅ Layer created: $LAYER_ARN"
echo ""
echo "Layer ARN: $LAYER_ARN"
echo ""
echo "Update lambda-config.json with this layer ARN"

# Cleanup
cd -
rm -rf "$TEMP_DIR"

