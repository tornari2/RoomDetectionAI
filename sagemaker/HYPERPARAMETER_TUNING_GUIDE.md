# YOLOv8 Hyperparameter Tuning Guide for Room Detection
# Comprehensive guide to maximize performance on architectural floor plans

## Overview

This guide provides detailed strategies for tuning YOLOv8 hyperparameters to achieve superior performance on room detection tasks. The recommendations are specifically optimized for architectural floor plan datasets.

---

## Critical Hyperparameters for Maximum Performance

### 1. Loss Function Weights (MOST IMPORTANT!)

These are the **most impactful** hyperparameters for your performance:

#### Box Loss Weight (`box`)
- **Default**: 7.5
- **Recommended Range**: 7.0 - 9.0
- **Impact**: Controls how much the model prioritizes accurate bounding box localization
- **For Room Detection**: Use **higher values (8.0-8.5)** because precise room boundaries are critical
- **Tuning Strategy**: 
  - Start at 7.5, increase to 8.0 if boxes are inaccurate
  - Monitor `train/box_loss` - should decrease steadily
  - Higher values = better localization but may slow convergence

#### Classification Loss Weight (`cls`)
- **Default**: 0.5
- **Recommended Range**: 0.2 - 0.5
- **Impact**: Controls classification accuracy
- **For Room Detection**: Use **lower values (0.3-0.4)** because you only have one class
- **Tuning Strategy**: 
  - Since it's single-class, classification is less critical
  - Lower values allow model to focus more on localization
  - Monitor `train/cls_loss` - should be stable and low

#### DFL Loss Weight (`dfl`)
- **Default**: 1.5
- **Recommended Range**: 1.5 - 2.5
- **Impact**: Distribution Focal Loss for bounding box regression
- **For Room Detection**: Use **moderate values (1.5-2.0)**
- **Tuning Strategy**: 
  - Higher values help with precise box boundaries
  - Try 2.0 if boxes are slightly off
  - Monitor `train/dfl_loss`

**Recommended Loss Weight Combination for Room Detection:**
```yaml
box: 8.0      # Higher - accurate boxes critical
cls: 0.3      # Lower - single class, less important  
dfl: 2.0      # Moderate - helps with box precision
```

---

### 2. Learning Rate Configuration

#### Initial Learning Rate (`lr0`)
- **Default**: 0.01
- **Recommended Range**: 0.005 - 0.02
- **Impact**: Controls training speed and stability
- **Strategy**: 
  - Start with 0.01
  - If training is unstable (loss spikes), reduce to 0.005
  - If training is too slow, increase to 0.015

#### Final Learning Rate (`lrf`)
- **Default**: 0.01 (means final LR = lr0 * 0.01)
- **Recommended Range**: 0.005 - 0.02
- **Impact**: Controls how much LR decays
- **Strategy**: 
  - Lower values (0.005) = slower decay, more training
  - Higher values (0.02) = faster decay, quicker convergence
  - For 300 epochs, use 0.01

#### Cosine LR Scheduler (`cos_lr`)
- **Default**: False
- **Recommended**: **True**
- **Impact**: Smooth learning rate decay
- **Why**: Better convergence than step decay, especially for longer training

#### Warmup Epochs (`warmup_epochs`)
- **Default**: 3
- **Recommended Range**: 3 - 5
- **Impact**: Gradual LR increase at start
- **Why**: Prevents early training instability

**Recommended LR Configuration:**
```yaml
lr0: 0.01
lrf: 0.01
cos_lr: true
warmup_epochs: 3
```

---

### 3. Data Augmentation (Key for Generalization!)

#### HSV Augmentation
- **`hsv_h`**: 0.015 (Hue) - Keep low for blueprints
- **`hsv_s`**: 0.7 (Saturation) - Higher for color variation
- **`hsv_v`**: 0.4 (Value) - Medium for brightness variation
- **Why**: Blueprints have consistent colors, but slight variations help

#### Geometric Augmentations
- **`translate`**: 0.1 - 0.15 (Translation)
  - Helps with alignment variations
  - Higher values = more variation
  
- **`scale`**: 0.5 - 0.6 (Scale)
  - **Critical** for handling different blueprint scales
  - Higher values = more scale variation
  
- **`fliplr`**: 0.5 (Horizontal flip)
  - Safe for floor plans
  - 50% probability is good
  
- **`degrees`**: 0.0 (Rotation)
  - **Keep at 0** - floor plans have specific orientation
  - Rotation would confuse the model
  
- **`shear`**: 0.0 (Shear)
  - **Keep at 0** - preserves rectangular room shapes
  
- **`perspective`**: 0.0 (Perspective)
  - **Keep at 0** - preserves floor plan geometry

#### Advanced Augmentations
- **`mosaic`**: 1.0 (Mosaic)
  - Combines 4 images into one
  - **Highly recommended** - improves generalization
  - Use `close_mosaic: 10` to disable in last 10 epochs
  
- **`mixup`**: 0.15 - 0.2 (Mixup)
  - Blends two images
  - **Recommended** - helps with generalization
  - Start with 0.15, increase to 0.2 if needed

**Recommended Augmentation Configuration:**
```yaml
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
translate: 0.1
scale: 0.5
fliplr: 0.5
mosaic: 1.0
mixup: 0.15
close_mosaic: 10
```

---

### 4. Optimizer Settings

#### Optimizer Type
- **SGD** (Recommended): Better for object detection, more stable
- **Adam/AdamW**: Faster convergence but may overfit
- **Strategy**: Start with SGD, try AdamW if SGD is too slow

#### Momentum (`momentum`)
- **Default**: 0.937
- **Recommended Range**: 0.9 - 0.95
- **Impact**: Helps accelerate convergence
- **Strategy**: Increase to 0.95 for faster training

#### Weight Decay (`weight_decay`)
- **Default**: 0.0005
- **Recommended Range**: 0.0001 - 0.001
- **Impact**: Prevents overfitting
- **Strategy**: Increase to 0.001 if overfitting, decrease if underfitting

**Recommended Optimizer Configuration:**
```yaml
optimizer: "SGD"
momentum: 0.937
weight_decay: 0.0005
```

---

### 5. Training Configuration

#### Epochs
- **Default**: 100
- **Recommended**: **300** for maximum performance
- **Why**: More epochs = better convergence
- **With Early Stopping**: Safe to use high values (patience will stop early)

#### Batch Size
- **Default**: 16
- **Recommended Range**: 16 - 32
- **Trade-off**: 
  - Larger batches (32) = more stable gradients, faster training
  - Smaller batches (16) = more gradient updates per epoch
- **For ml.g4dn.xlarge**: Can use 32 if memory allows

#### Image Size
- **Default**: 640
- **Recommended Range**: 640 - 800
- **Trade-off**:
  - 640 = faster training, good accuracy
  - 800 = better accuracy, slower training
- **Strategy**: Start with 640, try 800 if accuracy needs improvement

#### Early Stopping Patience
- **Default**: 50
- **Recommended**: **100** for longer training
- **Impact**: Prevents overfitting, saves time
- **Strategy**: Higher patience = more epochs before stopping

**Recommended Training Configuration:**
```yaml
epochs: 300
batch_size: 16  # or 32 if memory allows
img_size: 640   # or 800 for better accuracy
patience: 100
```

---

## Advanced Techniques for Competitive Advantage

### 1. Multi-Scale Training
```yaml
multi_scale: true
```
- **Impact**: Trains on multiple image sizes
- **Gain**: +0.5-1% mAP
- **Cost**: ~20% slower training
- **When to use**: If you need every bit of accuracy

### 2. Automatic Mixed Precision (AMP)
```yaml
amp: true
```
- **Impact**: Faster training, less memory
- **Gain**: 1.5-2x speedup
- **Cost**: Minimal accuracy loss
- **Always use**: Yes, recommended

### 3. Test-Time Augmentation (TTA)
- **Not in training config** - use during inference
- **Impact**: Average predictions from multiple augmentations
- **Gain**: +1-2% mAP
- **Cost**: Slower inference

### 4. Ensemble Models
- Train multiple models (YOLOv8s, YOLOv8m, YOLOv8l)
- Combine predictions with weighted voting
- **Gain**: +2-3% mAP
- **Cost**: 3x training time

### 5. Longer Training with Cosine LR
- Train for 300-500 epochs
- Use cosine LR scheduler
- Increase patience to 100-150
- **Gain**: +1-2% mAP
- **Cost**: Longer training time

---

## Hyperparameter Tuning Strategy

### Phase 1: Baseline (Week 1)
1. Use `performance_optimized` configuration
2. Train for 300 epochs
3. Establish baseline mAP50 (expect 0.85-0.90)

### Phase 2: Learning Rate Tuning (Week 2)
1. Try different LR schedules:
   - `lr0: 0.005, lrf: 0.01` (slower start)
   - `lr0: 0.015, lrf: 0.01` (faster start)
   - `lr0: 0.01, lrf: 0.005` (slower decay)
2. Keep best performing

### Phase 3: Loss Weight Tuning (Week 2-3)
1. Try different combinations:
   - `box: 8.0, cls: 0.3, dfl: 2.0` (aggressive)
   - `box: 7.5, cls: 0.5, dfl: 1.5` (balanced)
   - `box: 9.0, cls: 0.2, dfl: 2.5` (very aggressive)
2. Monitor validation mAP50
3. Keep best combination

### Phase 4: Augmentation Tuning (Week 3)
1. Try different augmentation strengths:
   - More aggressive: `scale: 0.6, translate: 0.15, mixup: 0.2`
   - Less aggressive: `scale: 0.4, translate: 0.1, mixup: 0.1`
2. Monitor validation loss (should decrease)
3. Keep best configuration

### Phase 5: Model Size (Week 4)
1. Try larger models:
   - YOLOv8m (better accuracy)
   - YOLOv8l (best accuracy)
2. Compare accuracy vs speed trade-off
3. Choose based on requirements

---

## Monitoring and Evaluation

### Key Metrics to Watch

1. **mAP50** (Primary metric)
   - Target: >0.90 for competitive performance
   - Monitor: Should increase steadily

2. **mAP50-95** (Stricter metric)
   - Target: >0.70
   - More challenging metric

3. **Precision**
   - Target: >0.90
   - Low false positives

4. **Recall**
   - Target: >0.85
   - Low false negatives

5. **Box Loss**
   - Should decrease steadily
   - If increasing = overfitting or LR too high

6. **Class Loss**
   - Should be low and stable (single class)

### Early Stopping Criteria

- Stop if validation mAP50 doesn't improve for `patience` epochs
- Stop if validation loss increases for 20+ epochs
- Stop if training loss is very low (<0.01) but validation loss is high (overfitting)

---

## Quick Reference: Best Configuration

```yaml
# Maximum Performance Configuration
epochs: 300
batch_size: 16
img_size: 640
lr0: 0.01
lrf: 0.01
cos_lr: true
warmup_epochs: 3
optimizer: "SGD"
momentum: 0.937
weight_decay: 0.0005
box: 8.0
cls: 0.3
dfl: 2.0
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
translate: 0.1
scale: 0.5
fliplr: 0.5
mosaic: 1.0
mixup: 0.15
close_mosaic: 10
patience: 100
amp: true
multi_scale: false
```

---

## Expected Performance

With optimized hyperparameters:
- **mAP50**: 0.88 - 0.93
- **mAP50-95**: 0.70 - 0.78
- **Precision**: 0.90 - 0.95
- **Recall**: 0.85 - 0.92

This should put you in the **top tier** of competitors using the same dataset!

