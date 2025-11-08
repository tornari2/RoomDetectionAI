# Folder Selection Guide for Training Data

## Current Situation

The COCO annotations include **all three folders**:
- **high_quality**: 825 images (19.6%)
- **high_quality_architectural**: 3,217 images (76.6%) 
- **colorful**: 158 images (3.8%)

**Total: 4,200 images** in the train set

## Analysis Results

Based on the comparison script (`compare_folders.py`):

### High Quality Folder
- **Average rooms**: 8.6 per image
- **Characteristics**: Similar color variance to other folders (~48)
- **Your PRD originally recommended**: ✅ Use this folder
- **Rationale**: Cleanest blueprint format, minimal distractions

### High Quality Architectural Folder  
- **Average rooms**: 14.4 per image (more complex layouts)
- **Characteristics**: Similar to high_quality (~51 color variance)
- **Your PRD originally recommended**: ❌ Exclude
- **Rationale**: More detailed architectural diagrams, potentially more text/annotations
- **BUT**: This is 76.6% of your dataset!

### Colorful Folder
- **Average rooms**: 11.2 per image  
- **Characteristics**: Slightly higher color variance (~54)
- **Your PRD originally recommended**: ❌ Exclude
- **Rationale**: Colored images may not match real-world blueprint characteristics

## Recommendation: Use ALL Folders (with validation)

### Why Include Everything:

1. **More Training Data = Better Model**
   - 4,200 images vs 825 images = 5x more data
   - Deep learning models benefit from more diverse data
   - YOLOv8 can handle variation in image characteristics

2. **The COCO Annotations Are Already There**
   - Someone already validated and created annotations for all folders
   - If they're in the COCO dataset, they're likely usable
   - Your time is better spent training than filtering

3. **Real-World Robustness**
   - Including varied styles makes your model more robust
   - It will handle different blueprint styles better
   - Architectural diagrams might actually help with complex layouts

### Validation Strategy:

1. **Review the comparison samples** (`folder_comparison/` directory)
   - Check if annotations look accurate across all folders
   - Verify bounding boxes are correct
   - Look for any obvious quality issues

2. **Start with all folders, monitor training**
   - Train with all 4,200 images
   - Monitor validation loss/metrics
   - If certain folders cause issues, filter them out later

3. **Use folder filtering script if needed**
   - The `coco_to_yolo_filtered.py` script lets you filter by folder
   - You can always retrain with a subset if needed

## Usage Examples

### Option 1: Use ALL folders (Recommended)
```bash
python3 coco_to_yolo_filtered.py \
  --coco-json train_coco_pt.json \
  --output-dir ./yolo_labels/train \
  --rooms-only
```

### Option 2: Use only high_quality (Original PRD approach)
```bash
python3 coco_to_yolo_filtered.py \
  --coco-json train_coco_pt.json \
  --output-dir ./yolo_labels/train \
  --rooms-only \
  --include-folders high_quality
```

### Option 3: Exclude colorful folder
```bash
python3 coco_to_yolo_filtered.py \
  --coco-json train_coco_pt.json \
  --output-dir ./yolo_labels/train \
  --rooms-only \
  --exclude-folders colorful
```

## My Recommendation

**Use ALL folders** for these reasons:

1. ✅ **5x more training data** (4,200 vs 825 images)
2. ✅ **Annotations already validated** by dataset creators
3. ✅ **Better model robustness** with varied styles
4. ✅ **Can filter later** if specific folders cause issues
5. ✅ **YOLOv8 handles variation well** - it's designed for diverse data

The original PRD recommendation to exclude folders was based on manual SVG parsing concerns. Since you're using pre-validated COCO annotations, those concerns don't apply.

**Action**: Review the `folder_comparison/` samples visually, then proceed with all folders unless you see major quality issues.

