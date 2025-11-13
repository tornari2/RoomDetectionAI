# Annotation Summary Report

## Image Type
**All images are original images (F1_original.png), NOT resized images.**

The annotations were created on the original blueprint images with varying resolutions.

## Dataset Statistics

### Train Dataset
- **Total images**: 4,200
- **Images with room annotations**: 4,194
- **Images without annotations**: 6 (removed)
- **Total room annotations**: 49,673

### Validation Dataset
- **Total images**: 400
- **Images with room annotations**: 400
- **Images without annotations**: 0
- **Total room annotations**: 4,606

### Test Dataset
- **Total images**: 400
- **Images with room annotations**: 398
- **Images without annotations**: 2 (removed)
- **Total room annotations**: 4,833

## Images Removed (No Annotations)

### Train (6 images removed)
- Image ID 1002: Folder 4520
- Image ID 1531: Folder 6443
- Image ID 3463: Folder 9451
- Image ID 3489: Folder 6683
- Image ID 3620: Folder 1657
- Image ID 3656: Folder 10000

### Test (2 images removed)
- Image ID 48: Folder 6269
- Image ID 219: Folder 7705

## Duplicate Analysis

No duplicate folders found in the COCO annotation files. Each folder ID appears exactly once per dataset.

## Final Dataset

After cleanup:
- **Train**: 4,194 label files
- **Val**: 400 label files
- **Test**: 398 label files
- **Total**: 4,992 annotated images

All label files correspond to images that have at least one room annotation.
