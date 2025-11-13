# Scripts Directory

This directory contains organized utility scripts for the Room Detection AI project.

## Directory Structure

### `aws-utils/`
AWS deployment and management utilities:
- `check_*.py` - Various AWS resource checking scripts
- `deploy_*.py` - Deployment utilities
- `fix_*.py` - Fix scripts for AWS resources
- `get_fresh_logs.py` - CloudWatch log retrieval
- `inspect_model.py` - SageMaker model inspection
- `remove_layers.py` - Lambda layer management

### `data-processing/`
Data processing and annotation scripts:
- `accurate_labeling.py` - Accurate room labeling
- `auto_offset_correction.py` - Offset correction utilities
- `batch_label_accurate.py` - Batch accurate labeling
- `batch_label_blueprints.py` - Batch blueprint labeling
- `diagnose_alignment.py` - Alignment diagnosis
- `hybrid_labeling.py` - Hybrid labeling approach
- `png_based_detection.py` - PNG-based detection

### Root Scripts
Main utility scripts:
- `clean_and_report_annotations.py` - Annotation cleanup and reporting
- `create_image_paths_mapping.py` - Image path mapping generation
- `download_model_artifacts.py` - Model artifact download
- `evaluate_model_performance.py` - Model performance evaluation
- `evaluate_test_set.py` - Test set evaluation
- `expand_all_tasks.py` - Taskmaster task expansion
- `expand_tasks_direct.py` - Direct task expansion
- `fetch_training_logs.py` - Training log retrieval
- `fix_s3_structure.py` - S3 structure fixes
- `regenerate_validation_no_labels.py` - Validation regeneration
- `retry_task6.py` - Task retry utility
- `setup_codebuild.py` - CodeBuild setup
- `validate_annotations.py` - Annotation validation

## Usage

Scripts are organized by purpose. Most scripts can be run directly:

```bash
# AWS utilities
python3 scripts/aws-utils/check_if_ready.py

# Data processing
python3 scripts/data-processing/batch_label_blueprints.py <args>

# Evaluation
python3 scripts/evaluate_test_set.py
```

## Notes

- The `coco_to_yolo.py` script remains in the project root as it's referenced by shell scripts
- Scripts in `other/` directory are kept for reference/archival purposes
- Application code (lambda/, api/, sagemaker/) remains in their respective directories

