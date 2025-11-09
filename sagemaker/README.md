# SageMaker Training Setup

This directory contains the necessary files for training YOLOv8 models on Amazon SageMaker.

## Directory Structure

```
sagemaker/
├── Dockerfile              # Custom container definition for YOLOv8
├── train.py               # Training script executed in container
├── requirements.txt       # Python dependencies
├── config/
│   └── training-config.yaml  # Training job configuration
└── outputs/               # Training outputs (gitignored)
    └── model_artifacts/   # Saved model artifacts
```

## Files Overview

### Dockerfile
- Based on SageMaker PyTorch container
- Installs YOLOv8 (ultralytics) and dependencies
- Sets up the training environment

### train.py
- Main training script executed by SageMaker
- Handles data loading, model training, and artifact saving
- Supports hyperparameter configuration
- Saves training metrics to JSON

### requirements.txt
- Python dependencies for YOLOv8 training
- Includes PyTorch, ultralytics, OpenCV, etc.

### training-config.yaml
- Training job configuration
- Instance type, hyperparameters, S3 paths
- Cost estimation included

## Setup Steps

1. **Build and Push Docker Container**
   ```bash
   # Authenticate to AWS public ECR (for base image)
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.us-east-1.amazonaws.com
   
   # Authenticate to your ECR (for pushing your image)
   aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 971422717446.dkr.ecr.us-east-2.amazonaws.com
   
   # Build container (use --platform linux/amd64 for Apple Silicon Macs)
   docker build --platform linux/amd64 -t room-detection-yolov8:latest sagemaker/
   
   # Tag for ECR
   docker tag room-detection-yolov8:latest 971422717446.dkr.ecr.us-east-2.amazonaws.com/room-detection-yolov8:latest
   
   # Push to ECR
   docker push 971422717446.dkr.ecr.us-east-2.amazonaws.com/room-detection-yolov8:latest
   ```
   
   **Note:** If you're on an Apple Silicon Mac, use `--platform linux/amd64` to build for SageMaker's x86_64 instances. This is normal and expected.

2. **Upload Training Data to S3**
   ```bash
   ./scripts/upload_training_data_to_s3.sh
   ```

3. **Create Training Job**
   - Use SageMaker Python SDK or AWS Console
   - Reference the container image URI
   - Configure input channels (training, validation)
   - Set hyperparameters from training-config.yaml

## Training Data Format

The training script expects data in YOLOv8 format:
- Images: `images/*.png`
- Labels: `labels/*.txt` (YOLO format)

Data structure in S3:
```
s3://bucket/training/
├── images/
│   ├── 1234_F1_original.png
│   └── ...
└── labels/
    ├── 1234_F1_original.txt
    └── ...
```

## Hyperparameters

Default hyperparameters (can be overridden):
- `epochs`: 100
- `batch_size`: 16
- `img_size`: 640
- `learning_rate`: 0.01
- `model_size`: yolov8s.pt
- `patience`: 50 (early stopping)

## Outputs

After training, the following are saved:
- Model artifacts: `/opt/ml/model/model.pt`
- Training metrics: `/opt/ml/output/training_metrics.json`
- Training logs: CloudWatch Logs

## Cost Estimation

- Instance: ml.g4dn.xlarge ($0.736/hour)
- Estimated training time: 4 hours
- Estimated cost: ~$2.94 per training run

## Next Steps

After completing this setup:
1. Test the container locally (optional)
2. Upload training data to S3
3. Create and run SageMaker training job
4. Monitor training in CloudWatch
5. Evaluate model performance

