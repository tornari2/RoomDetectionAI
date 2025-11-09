# Training Job Fix - Summary

## Date: November 8, 2025

## Issues Encountered

### Issue 1: S3 Path Double Slashes
**Error**: `s3://room-detection-ai-blueprints-dev/training/test//images/1025_F1_original.png has an illegal char sub-sequence '//' in it`

**Root Cause**: Test data located at `training/test/` was being downloaded along with training data, and paths had double slashes.

**Solution**: 
- Created `scripts/fix_s3_structure.py` to analyze and fix S3 structure
- Moved 796 test files from `training/test/` to `test/` (outside training prefix)
- Added path normalization to `sagemaker/scripts/run_training.py`
- Implemented `TrainingInput` for proper S3 path handling

### Issue 2: Argument Conflict in train.py
**Error**: `argparse.ArgumentError: argument --val: conflicting option string: --val`

**Root Cause**: The training script `sagemaker/train.py` defined `--val` twice:
- Line 25: `--val` as validation data directory (string)
- Line 96: `--val` as validation flag (boolean)

**Solution**:
- Renamed validation directory argument from `--val` to `--val-dir` (line 25)
- Updated all references to use `args.val_dir` instead of `args.val`
- Kept `--val` boolean flag for validation during training (line 96)

## Changes Made

### 1. S3 Structure (`scripts/fix_s3_structure.py`)
```bash
python3 scripts/fix_s3_structure.py --yes
```
- Fixed 0 double slashes (already cleaned)
- Moved 796 test files to proper location
- Verified clean structure

### 2. Training Script (`sagemaker/train.py`)
- Changed `--val` to `--val-dir` for validation directory
- Updated references:
  - `args.val` → `args.val_dir` (lines 144, 145, 158)
  - Kept `args.val` for boolean flag (line 252)

### 3. Launch Script (`sagemaker/scripts/run_training.py`)
- Added `TrainingInput` import
- Implemented path normalization function
- Updated input channels to use `TrainingInput` objects

### 4. Log Fetcher (`scripts/fetch_training_logs.py`)
- Created script to fetch CloudWatch logs
- Fixed API call to work without ordering by LastEventTime

## Current Training Job

**Job Name**: `yolov8-room-detection-20251108-215924`
**Status**: InProgress ✅
**Region**: us-east-2
**Instance**: ml.g4dn.xlarge
**Started**: 2025-11-08 22:00:11 UTC

### Configuration
- Epochs: 300
- Batch size: 16
- Image size: 640
- Model: yolov8s.pt
- Optimizer: SGD
- Learning rate: 0.01 → 0.0001
- Training images: 4,194
- Validation images: 400

### Monitor Commands

**Check status**:
```bash
python3 sagemaker/scripts/monitor_training.py \
  --job-name yolov8-room-detection-20251108-215924 \
  --region us-east-2
```

**Watch continuously**:
```bash
python3 sagemaker/scripts/monitor_training.py \
  --job-name yolov8-room-detection-20251108-215924 \
  --region us-east-2 \
  --watch
```

**Fetch logs**:
```bash
python3 scripts/fetch_training_logs.py \
  --job-name yolov8-room-detection-20251108-215924 \
  --region us-east-2 \
  --limit 500
```

### AWS Console
https://console.aws.amazon.com/sagemaker/home?region=us-east-2#/jobs/yolov8-room-detection-20251108-215924

## Expected Timeline
- Estimated training time: ~6 hours
- Estimated cost: ~$4.42
- Max runtime: 12 hours

## Files Modified
1. `sagemaker/train.py` - Fixed argument conflict
2. `sagemaker/scripts/run_training.py` - Added TrainingInput
3. `scripts/fix_s3_structure.py` - Created (new)
4. `scripts/fetch_training_logs.py` - Created (new)

## Final S3 Structure
```
s3://room-detection-ai-blueprints-dev/
├── training/
│   ├── images/           # 4,194 files ✅
│   ├── labels/           # 4,194 files ✅
│   ├── validation/
│   │   ├── images/       # 400 files ✅
│   │   └── labels/       # 400 files ✅
│   └── outputs/          # Previous job outputs
└── test/                 # 796 files (moved) ✅
    ├── images/
    └── labels/
```

## Status
✅ All issues resolved
✅ S3 structure cleaned
✅ Training script fixed
✅ New training job running successfully

