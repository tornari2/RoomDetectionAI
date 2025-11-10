# Script Cleanup Analysis

## Summary
**KEEP**: 4 files (actively used in production/deployment)  
**REMOVE**: 40+ files (unused, duplicates, or one-time development scripts)

---

## ✅ KEEP - Production & Deployment Scripts

### Main Directory
1. **`coco_to_yolo.py`** - KEEP
   - Used for data preparation (documented in README)
   - Required for converting training data
   - Referenced in: README.md, scripts/convert_all_coco_to_yolo.sh

2. **`restart_frontend.sh`** - KEEP
   - Active utility for restarting dev server
   - Recently created/used

### Scripts Directory
3. **`scripts/convert_all_coco_to_yolo.sh`** - KEEP
   - Batch conversion utility
   - Uses coco_to_yolo.py
   - Documented in README

4. **`scripts/create_image_paths_mapping.py`** - KEEP
   - Creates mapping for training data
   - Part of data preparation pipeline

---

## 🗑️ REMOVE - Unused/Development Scripts

### Main Directory - One-Time Debug/Fix Scripts
These were created for specific debugging sessions and are no longer needed:

- `FINAL_FIX.py` - One-time fix script
- `add_status_endpoint.sh` - One-time infrastructure update
- `check_endpoint_config.py` - Debug script
- `check_if_ready.py` - Debug script
- `check_model_exists.py` - Debug script
- `check_sagemaker.py` - Debug script
- `check_sagemaker_logs.py` - Debug script
- `deploy_mock.py` - Testing/mock script
- `deploy_with_numpy.py` - One-time deployment fix
- `fix_api_gateway.sh` - One-time infrastructure fix
- `fix_lambda_layer.py` - One-time fix
- `fix_sagemaker_endpoint.py` - One-time fix
- `get_fresh_logs.py` - Debug utility
- `inspect_model.py` - Debug utility
- `remove_layers.py` - One-time operation

### Main Directory - Old Data Labeling Scripts (Moved to /other)
These have duplicates in `/other` folder:

- `accurate_labeling.py` - DUPLICATE (exists in /other)
- `auto_offset_correction.py` - DUPLICATE (exists in /other)
- `batch_label_accurate.py` - DUPLICATE (exists in /other)
- `batch_label_blueprints.py` - DUPLICATE (exists in /other)
- `diagnose_alignment.py` - DUPLICATE (exists in /other)
- `hybrid_labeling.py` - DUPLICATE (exists in /other)
- `png_based_detection.py` - DUPLICATE (exists in /other)

### Scripts Directory - Build/Infrastructure (CodeBuild not used)
These were for CodeBuild setup which was abandoned:

- `scripts/build_with_codebuild.sh`
- `scripts/check_build_and_deploy.sh`
- `scripts/check_build_status.sh`
- `scripts/setup_codebuild.py`
- `scripts/create_codebuild_role.sh`

### Scripts Directory - Lambda Infrastructure (One-time setup)
These were for initial Lambda setup:

- `scripts/create_lambda_layer.sh` - Using Klayers instead
- `scripts/create_lambda_role.sh` - Using CloudFormation instead

### Scripts Directory - S3/Training Utilities (One-time use)
- `scripts/fix_s3_paths.sh` - One-time fix
- `scripts/fix_s3_structure.py` - One-time fix
- `scripts/fix_sagemaker_model.py` - Debug script
- `scripts/upload_training_data_to_s3.sh` - One-time upload (data already uploaded)

### Scripts Directory - Training/Monitoring (Not using SageMaker training anymore)
- `scripts/download_model_artifacts.py`
- `scripts/evaluate_model_performance.py`
- `scripts/fetch_training_logs.py`
- `scripts/retry_task6.py`

### Scripts Directory - Annotation/Validation (Data already prepared)
- `scripts/clean_and_report_annotations.py`
- `scripts/regenerate_validation_no_labels.py`
- `scripts/validate_annotations.py`

### Scripts Directory - Taskmaster Development Scripts
- `scripts/expand_all_tasks.py` - Taskmaster utility
- `scripts/expand_tasks_direct.py` - Taskmaster utility

### Other Directory - ALL FILES (Old Development Scripts)
The entire `/other` directory can be removed. It contains:
- Old labeling/annotation scripts from development phase
- Duplicate scripts (also in main directory)
- Analysis scripts used once during dataset creation
- PRD document that's now replaced

**Files in /other:**
- accurate_labeling.py
- analyze_coco_annotations.py
- analyze_dataset.py
- auto_offset_correction.py
- batch_label_accurate.py
- batch_label_blueprints.py
- check_svg_offset.py
- coco_to_yolo_filtered.py
- coco_to_yolo.py (duplicate)
- compare_folders.py
- diagnose_alignment.py
- extract_rooms_from_svg.py
- hybrid_labeling.py
- innergy_prd_enhanced.md
- png_based_detection.py
- README.md
- svg_to_training_data.py
- test_extraction.py
- visualize_boxes.py
- visualize_coco_samples.py
- wall_detection.py

---

## Recommended Cleanup Commands

```bash
# Main directory - Remove one-time debug/fix scripts
rm FINAL_FIX.py add_status_endpoint.sh check_*.py \
   deploy_mock.py deploy_with_numpy.py fix_*.py fix_*.sh \
   get_fresh_logs.py inspect_model.py remove_layers.py

# Main directory - Remove duplicate labeling scripts
rm accurate_labeling.py auto_offset_correction.py \
   batch_label_*.py diagnose_alignment.py \
   hybrid_labeling.py png_based_detection.py

# Scripts directory - Remove CodeBuild scripts
rm scripts/build_with_codebuild.sh scripts/check_build*.sh \
   scripts/setup_codebuild.py scripts/create_codebuild_role.sh

# Scripts directory - Remove Lambda setup scripts
rm scripts/create_lambda_layer.sh scripts/create_lambda_role.sh

# Scripts directory - Remove one-time fix scripts
rm scripts/fix_s3_*.sh scripts/fix_s3_*.py scripts/fix_sagemaker_model.py

# Scripts directory - Remove training/monitoring scripts
rm scripts/download_model_artifacts.py scripts/evaluate_model_performance.py \
   scripts/fetch_training_logs.py scripts/retry_task6.py

# Scripts directory - Remove annotation scripts
rm scripts/clean_and_report_annotations.py \
   scripts/regenerate_validation_no_labels.py \
   scripts/validate_annotations.py

# Scripts directory - Remove Taskmaster scripts
rm scripts/expand_*_tasks.py

# Scripts directory - Remove training upload script (data already uploaded)
rm scripts/upload_training_data_to_s3.sh

# Remove entire /other directory
rm -rf other/

# Remove __pycache__ directories
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

---

## Final Directory Structure After Cleanup

```
.
├── coco_to_yolo.py                  # ✅ KEEP - Data conversion
├── restart_frontend.sh              # ✅ KEEP - Dev utility
├── scripts/
│   ├── convert_all_coco_to_yolo.sh # ✅ KEEP - Batch conversion
│   └── create_image_paths_mapping.py # ✅ KEEP - Data preparation
└── [all other scripts removed]
```

---

## Benefits of Cleanup

1. **Reduced clutter**: From 40+ scripts to 4 essential ones
2. **Clear purpose**: Each remaining script has a documented use case
3. **Easier maintenance**: No confusion about which scripts to use
4. **Smaller repository**: ~50 files removed
5. **Better developer experience**: New developers can focus on what matters

---

## Notes

- All removed scripts were either:
  - One-time use (debugging, fixes, setup)
  - Duplicates (moved to /other then not used)
  - Part of abandoned approaches (CodeBuild)
  - Development-phase tools no longer needed
  
- The production system only uses:
  - Lambda handler code (in /lambda directory)
  - Frontend React app (in /frontend directory)  
  - CloudFormation templates (in /aws directory)
  - SageMaker training code (in /sagemaker directory)
  - Data preparation: coco_to_yolo.py and related scripts

- If you ever need the old scripts, they're in Git history

