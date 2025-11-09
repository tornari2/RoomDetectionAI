# Blueprint-Safe Augmentation Guide
# Which augmentations are safe vs risky for architectural floor plans

## ⚠️ RISKY Augmentations (Avoid or Use Minimally)

### 1. **Rotation (`degrees`)**
- **Risk Level**: 🔴 HIGH
- **Why Risky**: Floor plans have specific orientation (north-up convention)
- **Impact**: Model learns wrong orientation, confuses room relationships
- **Recommendation**: **Keep at 0.0** ✅

### 2. **Shear (`shear`)**
- **Risk Level**: 🔴 HIGH
- **Why Risky**: Distorts rectangular room shapes into parallelograms
- **Impact**: Model learns distorted shapes, hurts bounding box accuracy
- **Recommendation**: **Keep at 0.0** ✅

### 3. **Perspective (`perspective`)**
- **Risk Level**: 🔴 HIGH
- **Why Risky**: Distorts floor plan geometry (rooms become trapezoids)
- **Impact**: Breaks spatial relationships, hurts accuracy
- **Recommendation**: **Keep at 0.0** ✅

### 4. **Vertical Flip (`flipud`)**
- **Risk Level**: 🟡 MEDIUM
- **Why Risky**: Changes orientation (north becomes south)
- **Impact**: Confuses spatial relationships
- **Recommendation**: **Keep at 0.0** ✅

### 5. **High Hue Variation (`hsv_h`)**
- **Risk Level**: 🟡 MEDIUM
- **Why Risky**: Blueprints have specific colors (blue lines, white background)
- **Impact**: Unrealistic color shifts confuse model
- **Recommendation**: **Keep LOW (0.0-0.01)** ✅

### 6. **Mixup (`mixup`)**
- **Risk Level**: 🟡 MEDIUM-HIGH
- **Why Risky**: Blends two floor plans = unrealistic room layouts
- **Impact**: Creates impossible room combinations
- **Recommendation**: **Use LOW (0.0-0.1) or disable** ⚠️

### 7. **Mosaic (`mosaic`)**
- **Risk Level**: 🟡 MEDIUM
- **Why Risky**: Combines 4 floor plans = unrealistic layouts
- **Impact**: Creates impossible spatial relationships
- **Recommendation**: **Use with caution (0.5-0.8) or disable** ⚠️

---

## ✅ SAFE Augmentations (Recommended)

### 1. **Horizontal Flip (`fliplr`)**
- **Risk Level**: ✅ SAFE
- **Why Safe**: Floor plans can be mirrored left-right
- **Benefit**: Doubles training data, improves generalization
- **Recommendation**: **Use 0.5 (50% probability)** ✅

### 2. **Translation (`translate`)**
- **Risk Level**: ✅ SAFE
- **Why Safe**: Handles alignment variations, cropping differences
- **Benefit**: Robust to different image alignments
- **Recommendation**: **Use 0.05-0.1 (moderate)** ✅

### 3. **Scale (`scale`)**
- **Risk Level**: ✅ SAFE
- **Why Safe**: Blueprints come in different scales (1:50, 1:100, etc.)
- **Benefit**: Critical for handling scale variations
- **Recommendation**: **Use 0.3-0.5 (moderate-high)** ✅

### 4. **HSV Saturation (`hsv_s`)**
- **Risk Level**: ✅ SAFE (moderate)
- **Why Safe**: Handles color variations (blueprint vs colored plans)
- **Benefit**: Generalizes to different blueprint styles
- **Recommendation**: **Use 0.5-0.7 (moderate)** ✅

### 5. **HSV Value/Brightness (`hsv_v`)**
- **Risk Level**: ✅ SAFE
- **Why Safe**: Handles brightness variations (scan quality, lighting)
- **Benefit**: Robust to different image qualities
- **Recommendation**: **Use 0.3-0.4 (moderate)** ✅

---

## 📊 Recommended Configurations

### Configuration 1: **Conservative (Safest)**
```yaml
# Safe augmentations only
hsv_h: 0.0           # No hue change
hsv_s: 0.5           # Moderate saturation
hsv_v: 0.3           # Moderate brightness
degrees: 0.0         # No rotation
translate: 0.05      # Small translation
scale: 0.3           # Moderate scale
shear: 0.0           # No shear
perspective: 0.0     # No perspective
flipud: 0.0          # No vertical flip
fliplr: 0.5          # Horizontal flip (safe)
mosaic: 0.0          # No mosaic
mixup: 0.0           # No mixup
```

**Use when**: 
- You want maximum safety
- Dataset is already diverse
- You're unsure about augmentation impact

### Configuration 2: **Balanced (Recommended)**
```yaml
# Safe augmentations + minimal risky ones
hsv_h: 0.01          # Very small hue change
hsv_s: 0.6           # Moderate saturation
hsv_v: 0.4           # Moderate brightness
degrees: 0.0         # No rotation
translate: 0.1       # Moderate translation
scale: 0.5           # Moderate scale
shear: 0.0           # No shear
perspective: 0.0     # No perspective
flipud: 0.0          # No vertical flip
fliplr: 0.5          # Horizontal flip
mosaic: 0.5          # Moderate mosaic (use with caution)
mixup: 0.05          # Very low mixup (use with caution)
close_mosaic: 20     # Disable mosaic in last 20 epochs
```

**Use when**:
- You want good generalization
- Dataset could benefit from more variation
- You're monitoring validation metrics closely

### Configuration 3: **Aggressive (Use with Caution)**
```yaml
# More aggressive augmentations
hsv_h: 0.015         # Small hue change
hsv_s: 0.7           # Higher saturation
hsv_v: 0.4           # Moderate brightness
degrees: 0.0         # Still no rotation!
translate: 0.15      # Higher translation
scale: 0.6           # Higher scale
shear: 0.0           # Still no shear!
perspective: 0.0     # Still no perspective!
flipud: 0.0          # Still no vertical flip!
fliplr: 0.5          # Horizontal flip
mosaic: 0.8          # Higher mosaic
mixup: 0.1           # Low mixup
close_mosaic: 15     # Disable mosaic in last 15 epochs
```

**Use when**:
- You have limited data
- You're willing to experiment
- You're closely monitoring for degradation

---

## 🎯 Best Practice Recommendations

### For Your Room Detection Task:

1. **Always Safe**:
   - ✅ Horizontal flip (`fliplr: 0.5`)
   - ✅ Translation (`translate: 0.05-0.1`)
   - ✅ Scale (`scale: 0.3-0.5`)
   - ✅ HSV brightness (`hsv_v: 0.3-0.4`)

2. **Use Cautiously**:
   - ⚠️ Mosaic (`mosaic: 0.5-0.8`) - Monitor validation metrics
   - ⚠️ Mixup (`mixup: 0.0-0.1`) - Start with 0, increase if needed
   - ⚠️ HSV saturation (`hsv_s: 0.5-0.7`) - Moderate values

3. **Never Use**:
   - ❌ Rotation (`degrees: 0.0`)
   - ❌ Shear (`shear: 0.0`)
   - ❌ Perspective (`perspective: 0.0`)
   - ❌ Vertical flip (`flipud: 0.0`)
   - ❌ High hue variation (`hsv_h: >0.02`)

---

## 🔬 Testing Strategy

### Phase 1: Baseline (No Augmentation)
```yaml
# Minimal augmentation
fliplr: 0.5
translate: 0.05
scale: 0.3
hsv_v: 0.3
mosaic: 0.0
mixup: 0.0
```

### Phase 2: Add Safe Augmentations
```yaml
# Add more safe augmentations
fliplr: 0.5
translate: 0.1
scale: 0.5
hsv_s: 0.6
hsv_v: 0.4
mosaic: 0.0
mixup: 0.0
```

### Phase 3: Test Risky Augmentations (One at a Time)
```yaml
# Test mosaic
mosaic: 0.5
close_mosaic: 20

# Then test mixup
mixup: 0.05

# Monitor validation mAP50 - if it decreases, disable
```

---

## 📈 Expected Impact

### Conservative Augmentation:
- **Training stability**: ✅ High
- **Generalization**: 🟡 Moderate
- **Risk of degradation**: ✅ Low
- **Expected mAP50**: 0.85-0.90

### Balanced Augmentation:
- **Training stability**: ✅ High
- **Generalization**: ✅ Good
- **Risk of degradation**: 🟡 Low-Medium
- **Expected mAP50**: 0.88-0.92

### Aggressive Augmentation:
- **Training stability**: 🟡 Medium
- **Generalization**: ✅ Very Good
- **Risk of degradation**: 🟡 Medium
- **Expected mAP50**: 0.90-0.93 (if it works) or 0.80-0.85 (if it hurts)

---

## 💡 Key Insight

**For blueprints, LESS is often MORE.**

Unlike natural images where aggressive augmentation helps, blueprints have:
- Specific geometric constraints
- Important spatial relationships
- Consistent visual style

**Start conservative, then gradually add augmentations while monitoring validation metrics.**

If validation mAP50 decreases after adding an augmentation, **disable it immediately**.

