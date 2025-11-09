# SageMaker Training Job Launcher

This directory contains scripts for launching and monitoring SageMaker training jobs for the YOLOv8 room detection model.

## Files

- `run_training.py` - Python script to launch SageMaker training jobs (recommended)
- `run_training.sh` - Shell script alternative (simplified)
- `monitor_training.py` - Script to monitor training job progress

## Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **SageMaker Python SDK** installed:
   ```bash
   pip install sagemaker boto3 pyyaml
   ```
3. **Docker container built and pushed** to ECR (see `sagemaker/README.md`)
4. **Training data uploaded** to S3 (see `scripts/upload_training_data_to_s3.sh`)

## Quick Start

### 1. Dry Run (Validate Configuration)

```bash
python3 sagemaker/scripts/run_training.py --dry-run
```

This will validate your configuration without launching a job.

### 2. Launch Training Job

```bash
python3 sagemaker/scripts/run_training.py
```

The script will:
- Load configuration from `sagemaker/config/training-config.yaml`
- Auto-detect your SageMaker execution role
- Generate a unique job name with timestamp
- Launch the training job
- Print monitoring instructions

### 3. Monitor Training

```bash
# Check job status
python3 sagemaker/scripts/monitor_training.py --job-name <job-name>

# Or use AWS CLI
aws sagemaker describe-training-job --training-job-name <job-name>
```

## Command Line Options

### `run_training.py`

```bash
python3 sagemaker/scripts/run_training.py [OPTIONS]

Options:
  --config PATH       Path to training config YAML 
                      (default: sagemaker/config/training-config.yaml)
  --image-uri URI     ECR image URI (overrides config)
  --role ARN          SageMaker execution role ARN (auto-detected if not provided)
  --job-name NAME     Training job name (auto-generated if not provided)
  --dry-run           Print configuration without launching job
```

### Examples

```bash
# Use custom config file
python3 sagemaker/scripts/run_training.py --config sagemaker/config/training-config-conservative.yaml

# Specify custom image URI
python3 sagemaker/scripts/run_training.py --image-uri 763104351884.dkr.ecr.us-east-1.amazonaws.com/room-detection-yolov8:v1.0

# Custom job name
python3 sagemaker/scripts/run_training.py --job-name my-custom-training-run

# Dry run to validate config
python3 sagemaker/scripts/run_training.py --dry-run
```

## Configuration

The training configuration is defined in `sagemaker/config/training-config.yaml`. Key settings:

- **Instance type**: `ml.g4dn.xlarge` (GPU instance)
- **Hyperparameters**: Epochs, batch size, learning rate, etc.
- **S3 paths**: Training data, validation data, output paths
- **Container image**: ECR repository URI

## Monitoring

After launching a training job, you can monitor it in several ways:

### 1. AWS Console
```
https://console.aws.amazon.com/sagemaker/home?region=us-east-1#/jobs/<job-name>
```

### 2. CloudWatch Logs
```
/aws/sagemaker/TrainingJobs/<job-name>
```

### 3. AWS CLI
```bash
# Get job status
aws sagemaker describe-training-job --training-job-name <job-name>

# Wait for completion
aws sagemaker wait training-job-completed-or-stopped --training-job-name <job-name>

# Get training metrics
aws sagemaker describe-training-job --training-job-name <job-name> --query 'FinalMetricDataList'
```

### 4. Python Monitoring Script
```bash
python3 sagemaker/scripts/monitor_training.py --job-name <job-name>
```

## Training Outputs

After training completes, the following are saved:

1. **Model artifacts**: `s3://<bucket>/training/outputs/<job-name>/output/model.tar.gz`
   - Contains `model.pt` (best model weights)
   - Contains `training_metrics.json` (training metrics)

2. **CloudWatch Logs**: Training logs with metrics, loss values, etc.

3. **Training Metrics**: JSON file with:
   - Hyperparameters used
   - Final validation metrics (mAP, precision, recall)
   - Training loss values

## Cost Estimation

Based on configuration:
- **Instance**: ml.g4dn.xlarge ($0.736/hour)
- **Estimated time**: 6 hours (for 300 epochs)
- **Estimated cost**: ~$4.42 per training run

Actual costs may vary based on:
- Training duration (early stopping may reduce time)
- Data transfer costs
- Storage costs

## Troubleshooting

### Error: "Could not get SageMaker execution role"
- Ensure you're running from a SageMaker notebook instance, or
- Provide `--role` argument with your SageMaker execution role ARN

### Error: "Container image not found"
- Verify the Docker container is built and pushed to ECR
- Check the image URI in the config file
- Ensure you have permissions to access the ECR repository

### Error: "Training data not found in S3"
- Verify training data is uploaded to S3
- Check S3 bucket name and prefixes in config file
- Ensure data structure matches expected format (images/ and labels/ directories)

### Training job fails immediately
- Check CloudWatch logs for error messages
- Verify container can access S3 (IAM permissions)
- Ensure training script (`train.py`) is correct

## Next Steps

After training completes:

1. **Download model artifacts** from S3
2. **Evaluate model performance** using validation metrics
3. **Test model** on sample images
4. **Deploy model** to SageMaker endpoint (Task 6)

## Related Files

- `sagemaker/train.py` - Training script executed in container
- `sagemaker/config/training-config.yaml` - Training configuration
- `sagemaker/README.md` - SageMaker setup documentation
- `scripts/upload_training_data_to_s3.sh` - Data upload script

