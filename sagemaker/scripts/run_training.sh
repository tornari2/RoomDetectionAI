#!/bin/bash
# SageMaker Training Job Launcher (Shell Script)
# Alternative to Python script for launching SageMaker training jobs

set -e

# Default values
CONFIG_FILE="sagemaker/config/training-config.yaml"
REGION="us-east-1"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --config FILE    Path to training config YAML (default: sagemaker/config/training-config.yaml)"
            echo "  --region REGION  AWS region (default: us-east-1)"
            echo "  --dry-run        Print configuration without launching job"
            echo "  --help           Show this help message"
            echo ""
            echo "Note: This script requires AWS CLI and jq to be installed."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check dependencies
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI not found. Please install AWS CLI."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq not found. Please install jq (JSON processor)."
    exit 1
fi

if ! command -v yq &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "⚠️  Warning: yq not found. Will use Python to parse YAML."
fi

# Generate job name
JOB_NAME="yolov8-room-detection-$(date +%Y%m%d-%H%M%S)"

echo "📋 Launching SageMaker Training Job"
echo "   Job Name: $JOB_NAME"
echo "   Region: $REGION"
echo ""

# Note: This is a simplified version. For full functionality, use the Python script.
echo "⚠️  Note: This shell script is a simplified launcher."
echo "   For full functionality with hyperparameter configuration, use:"
echo "   python3 sagemaker/scripts/run_training.py"
echo ""
echo "💡 To launch training with this script, you'll need to:"
echo "   1. Extract configuration from YAML manually"
echo "   2. Use AWS CLI to create training job"
echo ""
echo "📖 Recommended: Use the Python script instead:"
echo "   python3 sagemaker/scripts/run_training.py --config $CONFIG_FILE"

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "✅ Dry run complete."
    exit 0
fi

# For now, just show instructions
echo ""
echo "To launch training, use the Python script:"
echo "  python3 sagemaker/scripts/run_training.py"

