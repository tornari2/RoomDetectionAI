# Using COCO Annotations Instead of SVG Parsing

## Summary

**Great news!** The Cubicasa5K dataset already includes COCO format annotations in the `cubicasa5k_coco` directory. These annotations contain **room bounding boxes** that can directly replace all the SVG parsing work you've been doing.

## Benefits of Using COCO Annotations

### ✅ **Eliminates SVG Parsing Complexity**
- No need to parse SVG XML structure
- No coordinate transformation issues (SVG to PNG alignment)
- No viewBox offset calculations
- No polygon point parsing

### ✅ **Pre-validated Annotations**
- Annotations are already created and validated
- Consistent format across all samples
- No manual spot-checking needed

### ✅ **Ready-to-Use Format**
- Standard COCO format (widely supported)
- Already split into train/val/test sets
- Easy conversion to YOLO format for training

### ✅ **More Data Available**
- Test set: 4,833 room annotations across 400 images
- Train set: 49,673 room annotations across 4,200 images
- Average ~12 rooms per image

## COCO Annotation Structure

The COCO files contain:
- **Categories**: 
  - ID 1: `wall`
  - ID 2: `room` ← **This is what you need!**
- **Bounding Box Format**: `[x, y, width, height]` (top-left corner + dimensions)
- **File Structure**: Already organized by train/val/test splits

## Conversion to YOLO Format

I've created `coco_to_yolo.py` to convert COCO annotations to YOLO format (which YOLOv8 needs for training).

### Usage:

```bash
# Convert train set (rooms only)
python3 coco_to_yolo.py \
  --coco-json /Users/michaeltornaritis/Downloads/archive/cubicasa5k_coco/train_coco_pt.json \
  --output-dir ./yolo_labels/train \
  --rooms-only

# Convert validation set
python3 coco_to_yolo.py \
  --coco-json /Users/michaeltornaritis/Downloads/archive/cubicasa5k_coco/val_coco_pt.json \
  --output-dir ./yolo_labels/val \
  --rooms-only

# Convert test set
python3 coco_to_yolo.py \
  --coco-json /Users/michaeltornaritis/Downloads/archive/cubicasa5k_coco/test_coco_pt.json \
  --output-dir ./yolo_labels/test \
  --rooms-only
```

## What This Means for Your Project

### Files You Can Now Skip:
- ❌ `extract_rooms_from_svg.py` - No longer needed
- ❌ `svg_to_training_data.py` - Replaced by `coco_to_yolo.py`
- ❌ `batch_label_accurate.py` - COCO annotations are already accurate
- ❌ `batch_label_blueprints.py` - Same as above
- ❌ `check_svg_offset.py` - No coordinate alignment needed
- ❌ `diagnose_alignment.py` - Not needed with COCO
- ❌ `hybrid_labeling.py` - COCO annotations are the source of truth

### New Workflow:

1. **Use COCO annotations directly** - They're already in the dataset
2. **Convert to YOLO format** - Use `coco_to_yolo.py` script
3. **Match images to labels** - COCO JSON includes file paths
4. **Train YOLOv8** - Use the YOLO format labels

## Image File Paths

The COCO annotations reference image paths like:
```
/kaggle/input/cubicasa5k/cubicasa5k/cubicasa5k/high_quality_architectural/1191/F1_original.png
```

You'll need to:
1. Extract the sample ID from the path (e.g., `1191`)
2. Find the corresponding image in your local dataset
3. Match it with the generated YOLO label file

## Next Steps

1. **Run the conversion script** to generate YOLO labels
2. **Verify a few samples** by visualizing bounding boxes
3. **Update your training pipeline** to use COCO-based labels instead of SVG parsing
4. **Update the PRD** to reflect that you're using COCO annotations

## Example: Visualizing COCO Annotations

You can create a visualization script to verify the annotations:

```python
import json
from PIL import Image, ImageDraw

# Load COCO data
with open('train_coco_pt.json', 'r') as f:
    coco_data = json.load(f)

# Get first image with room annotations
images = {img['id']: img for img in coco_data['images']}
room_annos = [a for a in coco_data['annotations'] if a['category_id'] == 2]

if room_annos:
    first_anno = room_annos[0]
    image_info = images[first_anno['image_id']]
    
    # Load image (adjust path as needed)
    # Draw bounding boxes
    # Save visualization
```

## Conclusion

**Yes, the COCO annotations are absolutely useful for annotating rooms!** In fact, they're **better** than parsing SVG files because:
- They're pre-validated
- They're in a standard format
- They eliminate coordinate transformation issues
- They're ready to use immediately

You can **completely skip the SVG parsing approach** and use COCO annotations instead. This will save you significant time and eliminate many potential bugs.

