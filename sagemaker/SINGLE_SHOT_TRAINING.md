# Single-Shot Training Configuration Summary
# Optimized for one training run with conservative augmentation

## Key Changes for Single-Shot Training

### ✅ Augmentation (Conservative - Safe Only)
- **Horizontal flip**: 0.5 (doubles data safely)
- **Translation**: 0.05 (small, safe)
- **Scale**: 0.3 (moderate, safe)
- **HSV brightness**: 0.3 (handles scan quality)
- **HSV saturation**: 0.5 (handles color variations)
- **NO risky augmentations**: mosaic=0, mixup=0, rotation=0, shear=0, perspective=0

### ✅ Hyperparameters (Optimized)
- **Loss weights**: box=8.0, cls=0.3, dfl=2.0 (optimized for room detection)
- **Learning rate**: 0.01 → 0.0001 (cosine decay)
- **Epochs**: 300 (compensates for less augmentation)
- **Patience**: 150 (higher since less augmentation)
- **Batch size**: 16 (stable)

### ✅ What's NOT Affected by Augmentation
- **Loss function weights** (box, cls, dfl) - These are about the TASK, not augmentation
- **Learning rate** - Independent of augmentation
- **Optimizer settings** - Independent of augmentation
- **Model architecture** - Independent of augmentation

### ✅ What IS Adjusted for Conservative Augmentation
- **Epochs**: 300 (more epochs compensate for less data variation)
- **Patience**: 150 (higher patience allows more training)
- **Weight decay**: 0.0005 (prevents overfitting with less augmentation)

## Training Strategy

1. **Start with this conservative config**
2. **Monitor validation mAP50** - should increase steadily
3. **Early stopping** will prevent overfitting (patience=150)
4. **Best model** will be saved automatically

## Expected Performance

With conservative augmentation:
- **Training stability**: ✅ Very High
- **Risk of degradation**: ✅ Very Low
- **Expected mAP50**: 0.85-0.92
- **Training time**: 4-6 hours
- **Cost**: $3-5

## Why This Works

- **Less augmentation = more stable training**
- **More epochs = compensates for less variation**
- **Higher patience = allows full convergence**
- **Optimized loss weights = task-specific optimization**

This configuration maximizes your chances of success in a single training run!

