#!/bin/bash
# Script to upload training data to S3
# Uploads images and labels in YOLOv8 format

set -e  # Exit on error

# Configuration
BUCKET_NAME="room-detection-ai-blueprints-dev"
REGION="us-east-2"
TRAINING_PREFIX="training"  # No trailing slash - will be appended correctly
VALIDATION_PREFIX="training/validation"  # No trailing slash

# Local paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"
YOLO_LABELS_DIR="$DATA_DIR/yolo_labels"

# Dataset root (where original images are stored)
DATASET_ROOT="${DATASET_ROOT:-/Users/michaeltornaritis/Downloads/archive/cubicasa5k/cubicasa5k}"

echo "=========================================="
echo "Uploading Training Data to S3"
echo "=========================================="
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"
echo "Dataset root: $DATASET_ROOT"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if dataset root exists
if [ ! -d "$DATASET_ROOT" ]; then
    echo "❌ Dataset root not found: $DATASET_ROOT"
    echo "Please set DATASET_ROOT environment variable or update this script."
    exit 1
fi

# Function to upload images and labels for a split
upload_split() {
    local split=$1
    local s3_prefix=$2
    
    echo ""
    echo "----------------------------------------"
    echo "Uploading $split split"
    echo "----------------------------------------"
    
    # Create temporary directory structure
    TEMP_DIR=$(mktemp -d)
    TEMP_IMAGES="$TEMP_DIR/images"
    TEMP_LABELS="$TEMP_DIR/labels"
    mkdir -p "$TEMP_IMAGES" "$TEMP_LABELS"
    
    # Copy label files
    echo "Copying label files..."
    cp "$YOLO_LABELS_DIR/$split"/*.txt "$TEMP_LABELS/" 2>/dev/null || {
        echo "⚠️  Warning: No label files found in $YOLO_LABELS_DIR/$split"
    }
    
    # Count label files
    LABEL_COUNT=$(ls -1 "$TEMP_LABELS"/*.txt 2>/dev/null | wc -l | tr -d ' ')
    echo "Found $LABEL_COUNT label files"
    
    # Copy corresponding images
    echo "Copying images..."
    IMAGE_COUNT=0
    
    # Read image_paths_mapping.json to find image paths
    if [ -f "$DATA_DIR/image_paths_mapping.json" ]; then
        echo "Using image_paths_mapping.json to locate images..."
        
        # Extract image paths for this split using Python
        python3 << EOF
import json
import os
import shutil
from pathlib import Path

with open('$DATA_DIR/image_paths_mapping.json', 'r') as f:
    mapping = json.load(f)

split = '$split'
dataset_root = Path('$DATASET_ROOT')
temp_images = Path('$TEMP_IMAGES')

count = 0
for item in mapping.get(split, []):
    coco_path = item['coco_image_path']
    # Extract folder and sample ID from COCO path
    parts = coco_path.split('/')
    folder_name = None
    sample_id = None
    
    for i, part in enumerate(parts):
        if part in ['high_quality', 'high_quality_architectural', 'colorful']:
            folder_name = part
            if i + 1 < len(parts):
                sample_id = parts[i + 1]
            break
    
    if folder_name and sample_id:
        image_path = dataset_root / folder_name / sample_id / 'F1_original.png'
        if image_path.exists():
            # Copy with consistent naming
            label_file = Path('$YOLO_LABELS_DIR') / split / f"{sample_id}_F1_original.txt"
            if label_file.exists():
                dest_name = f"{sample_id}_F1_original.png"
                shutil.copy2(image_path, temp_images / dest_name)
                count += 1
                if count % 100 == 0:
                    print(f"  Copied {count} images...")

print(f"Total images copied: {count}")
EOF
        IMAGE_COUNT=$(ls -1 "$TEMP_IMAGES"/*.png 2>/dev/null | wc -l | tr -d ' ')
    else
        echo "⚠️  Warning: image_paths_mapping.json not found. Skipping image copy."
        echo "You may need to upload images manually or create the mapping file first."
    fi
    
    echo "Found $IMAGE_COUNT images"
    
    # Upload to S3
    if [ "$IMAGE_COUNT" -gt 0 ] || [ "$LABEL_COUNT" -gt 0 ]; then
        echo ""
        echo "Uploading to S3..."
        
        # Upload images
        if [ "$IMAGE_COUNT" -gt 0 ]; then
            echo "Uploading images to s3://$BUCKET_NAME/$s3_prefix/images/"
            aws s3 sync "$TEMP_IMAGES" "s3://$BUCKET_NAME/$s3_prefix/images/" \
                --region "$REGION" \
                --exclude "*" --include "*.png" \
                --no-progress
        
            echo "✓ Uploaded $IMAGE_COUNT images"
        fi
        
        # Upload labels
        if [ "$LABEL_COUNT" -gt 0 ]; then
            echo "Uploading labels to s3://$BUCKET_NAME/$s3_prefix/labels/"
            aws s3 sync "$TEMP_LABELS" "s3://$BUCKET_NAME/$s3_prefix/labels/" \
                --region "$REGION" \
                --exclude "*" --include "*.txt" \
                --no-progress
        
            echo "✓ Uploaded $LABEL_COUNT label files"
        fi
    else
        echo "⚠️  No files to upload for $split split"
    fi
    
    # Cleanup
    rm -rf "$TEMP_DIR"
}

# Upload training data
upload_split "train" "$TRAINING_PREFIX"

# Upload validation data
upload_split "val" "$VALIDATION_PREFIX"

# Upload test data (optional, for evaluation)
read -p "Upload test data as well? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    upload_split "test" "training/test/"
fi

echo ""
echo "=========================================="
echo "Upload Complete!"
echo "=========================================="
echo ""
echo "Data uploaded to:"
echo "  Training: s3://$BUCKET_NAME/$TRAINING_PREFIX"
echo "  Validation: s3://$BUCKET_NAME/$VALIDATION_PREFIX"
echo ""
echo "Next steps:"
echo "  1. Build and push Docker container to ECR"
echo "  2. Create SageMaker training job"
echo "  3. Monitor training progress in CloudWatch"

