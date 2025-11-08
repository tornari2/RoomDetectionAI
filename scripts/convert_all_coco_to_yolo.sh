#!/bin/bash
# Convert all COCO annotation files to YOLO format
# This script processes train, val, and test COCO JSON files

set -e  # Exit on error

# Configuration
COCO_DIR="/Users/michaeltornaritis/Downloads/archive/cubicasa5k_coco"
OUTPUT_BASE_DIR="data/yolo_labels"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}COCO to YOLO Conversion Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Function to convert a single COCO file
convert_coco_file() {
    local coco_file=$1
    local output_dir=$2
    local dataset_name=$3
    
    if [ ! -f "$coco_file" ]; then
        echo "Error: COCO file not found: $coco_file"
        return 1
    fi
    
    echo -e "${GREEN}Converting $dataset_name dataset...${NC}"
    echo "  Input: $coco_file"
    echo "  Output: $output_dir"
    
    python3 coco_to_yolo.py \
        --coco-json "$coco_file" \
        --output-dir "$output_dir" \
        --rooms-only
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $dataset_name conversion completed${NC}"
        echo ""
    else
        echo "Error: Failed to convert $dataset_name"
        return 1
    fi
}

# Convert train dataset
convert_coco_file \
    "$COCO_DIR/train_coco_pt.json" \
    "$OUTPUT_BASE_DIR/train" \
    "train"

# Convert validation dataset
convert_coco_file \
    "$COCO_DIR/val_coco_pt.json" \
    "$OUTPUT_BASE_DIR/val" \
    "val"

# Convert test dataset
convert_coco_file \
    "$COCO_DIR/test_coco_pt.json" \
    "$OUTPUT_BASE_DIR/test" \
    "test"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All conversions completed!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Summary:"
echo "  Train labels: $OUTPUT_BASE_DIR/train"
echo "  Val labels:   $OUTPUT_BASE_DIR/val"
echo "  Test labels:  $OUTPUT_BASE_DIR/test"
echo ""

# Count files
train_count=$(find "$OUTPUT_BASE_DIR/train" -name "*.txt" | wc -l | tr -d ' ')
val_count=$(find "$OUTPUT_BASE_DIR/val" -name "*.txt" | wc -l | tr -d ' ')
test_count=$(find "$OUTPUT_BASE_DIR/test" -name "*.txt" | wc -l | tr -d ' ')

echo "File counts:"
echo "  Train: $train_count label files"
echo "  Val:   $val_count label files"
echo "  Test:  $test_count label files"

