#!/bin/bash
# Fix S3 double-slash issue by moving files to correct paths

set -e

BUCKET_NAME="room-detection-ai-blueprints-dev"
REGION="us-east-2"

echo "=========================================="
echo "Fixing S3 Double-Slash Paths"
echo "=========================================="
echo "This will move files from training// to training/"
echo ""

# Move training images
echo "Moving training images..."
aws s3 mv s3://$BUCKET_NAME/training//images/ s3://$BUCKET_NAME/training/images/ \
    --recursive --region $REGION

# Move training labels  
echo "Moving training labels..."
aws s3 mv s3://$BUCKET_NAME/training//labels/ s3://$BUCKET_NAME/training/labels/ \
    --recursive --region $REGION

# Move validation images
echo "Moving validation images..."
aws s3 mv s3://$BUCKET_NAME/training//validation/images/ s3://$BUCKET_NAME/training/validation/images/ \
    --recursive --region $REGION 2>/dev/null || \
aws s3 mv s3://$BUCKET_NAME/training/validation//images/ s3://$BUCKET_NAME/training/validation/images/ \
    --recursive --region $REGION 2>/dev/null || echo "Validation images already in correct location"

# Move validation labels
echo "Moving validation labels..."
aws s3 mv s3://$BUCKET_NAME/training//validation/labels/ s3://$BUCKET_NAME/training/validation/labels/ \
    --recursive --region $REGION 2>/dev/null || \
aws s3 mv s3://$BUCKET_NAME/training/validation//labels/ s3://$BUCKET_NAME/training/validation/labels/ \
    --recursive --region $REGION 2>/dev/null || echo "Validation labels already in correct location"

# Move test images (if they exist)
echo "Moving test images..."
aws s3 mv s3://$BUCKET_NAME/training//test/images/ s3://$BUCKET_NAME/training/test/images/ \
    --recursive --region $REGION 2>/dev/null || \
aws s3 mv s3://$BUCKET_NAME/training/test//images/ s3://$BUCKET_NAME/training/test/images/ \
    --recursive --region $REGION 2>/dev/null || echo "Test images already in correct location or don't exist"

# Move test labels (if they exist)
echo "Moving test labels..."
aws s3 mv s3://$BUCKET_NAME/training//test/labels/ s3://$BUCKET_NAME/training/test/labels/ \
    --recursive --region $REGION 2>/dev/null || \
aws s3 mv s3://$BUCKET_NAME/training/test//labels/ s3://$BUCKET_NAME/training/test/labels/ \
    --recursive --region $REGION 2>/dev/null || echo "Test labels already in correct location or don't exist"

echo ""
echo "=========================================="
echo "✅ S3 paths fixed!"
echo "=========================================="
echo ""
echo "You can now launch training again:"
echo "  python3 sagemaker/scripts/run_training.py --role <your-role-arn>"

