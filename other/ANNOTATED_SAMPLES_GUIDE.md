# Annotated Sample Images by Folder

This document shows annotated sample images from each folder in the Cubicasa5K dataset to help evaluate training data quality.

## Sample Images Location

All annotated samples are saved in the `folder_comparison/` directory:
- **high_quality**: 3 samples
- **high_quality_architectural**: 3 samples  
- **colorful**: 3 samples

## Folder Characteristics

### High Quality Folder
- **Total images**: 825 (19.6% of train set)
- **Average rooms per image**: ~8.3
- **Characteristics**: Standard blueprint format, clean layouts
- **Sample files**: 
  - `high_quality_sample_01_12290_annotated.png` (12 rooms)
  - `high_quality_sample_02_5879_annotated.png` (9 rooms)
  - `high_quality_sample_03_1712_annotated.png` (4 rooms)

### High Quality Architectural Folder
- **Total images**: 3,217 (76.6% of train set)
- **Average rooms per image**: ~8.0
- **Characteristics**: More detailed architectural diagrams, varied complexity
- **Sample files**:
  - `high_quality_architectural_sample_01_7598_annotated.png` (12 rooms)
  - `high_quality_architectural_sample_02_12617_annotated.png` (6 rooms)
  - `high_quality_architectural_sample_03_11180_annotated.png` (6 rooms)

### Colorful Folder
- **Total images**: 158 (3.8% of train set)
- **Average rooms per image**: ~5.3
- **Characteristics**: Colored floor plans, may have different visual style
- **Sample files**:
  - `colorful_sample_01_6296_annotated.png` (7 rooms)
  - `colorful_sample_02_2194_annotated.png` (6 rooms)
  - `colorful_sample_03_1740_annotated.png` (3 rooms)

## Visual Inspection Checklist

When reviewing these samples, check:

1. **Bounding Box Accuracy**
   - ✅ Boxes align with room boundaries
   - ✅ No major misalignments or offsets
   - ✅ Boxes are appropriately sized (not too large/small)

2. **Room Coverage**
   - ✅ All visible rooms are annotated
   - ✅ No obvious missing rooms
   - ✅ Consistent annotation quality

3. **Image Quality**
   - ✅ Images are clear and suitable for training
   - ✅ No excessive artifacts or blur
   - ✅ Appropriate resolution for model input

4. **Style Consistency**
   - ✅ Different folders show varied but usable styles
   - ✅ Annotations work across all folder types
   - ✅ No folder-specific annotation issues

## Recommendation

Based on visual inspection of these samples, **all three folders are recommended for training** because:
- Annotations appear accurate across all folders
- Provides 5x more training data (4,200 vs 825 images)
- Varied styles improve model robustness
- Pre-validated COCO annotations eliminate quality concerns

## Regenerating Samples

To regenerate comparison samples with different parameters:

```bash
python3 compare_folders.py \
  --coco-json /path/to/train_coco_pt.json \
  --dataset-root /path/to/cubicasa5k/cubicasa5k \
  --output-dir ./folder_comparison \
  --samples-per-folder 5
```

