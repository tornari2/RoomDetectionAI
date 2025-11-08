#!/usr/bin/env python3
"""
Convert COCO format annotations to YOLO format for room detection training.

This script replaces the SVG parsing approach by using pre-existing COCO annotations
from the cubicasa5k_coco dataset.
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def coco_bbox_to_yolo(bbox, img_width, img_height):
    """
    Convert COCO bbox format [x, y, width, height] to YOLO format [center_x, center_y, width, height].
    
    Args:
        bbox: COCO format bbox [x, y, width, height] in absolute pixels
        img_width: Image width in pixels
        img_height: Image height in pixels
    
    Returns:
        Tuple (center_x, center_y, width, height) normalized to 0-1
    """
    x, y, w, h = bbox
    
    # Calculate center coordinates
    center_x = (x + w / 2.0) / img_width
    center_y = (y + h / 2.0) / img_height
    
    # Normalize width and height
    width_norm = w / img_width
    height_norm = h / img_height
    
    return center_x, center_y, width_norm, height_norm

def convert_coco_to_yolo(coco_json_path, output_dir, category_filter=None):
    """
    Convert COCO format annotations to YOLO format label files.
    
    Args:
        coco_json_path: Path to COCO format JSON file
        output_dir: Directory to save YOLO format .txt label files
        category_filter: List of category IDs to include (None = all categories)
                       For rooms only, use [2]
    
    Returns:
        Dictionary with conversion statistics
    """
    # Load COCO annotations
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build mappings
    images = {img['id']: img for img in coco_data['images']}
    categories = {cat['id']: cat for cat in coco_data['categories']}
    
    # Filter annotations by category if specified
    annotations = coco_data['annotations']
    if category_filter:
        annotations = [ann for ann in annotations if ann['category_id'] in category_filter]
    
    # Group annotations by image_id
    annotations_by_image = defaultdict(list)
    for ann in annotations:
        annotations_by_image[ann['image_id']].append(ann)
    
    # Convert each image's annotations to YOLO format
    stats = {
        'total_images': len(images),
        'images_with_annotations': len(annotations_by_image),
        'total_annotations': len(annotations),
        'converted_files': 0
    }
    
    for image_id, image_info in images.items():
        img_width = image_info['width']
        img_height = image_info['height']
        file_name = image_info['file_name']
        
        # Get base filename without extension
        # Extract unique identifier from path (e.g., folder number) or use image_id
        path_parts = Path(file_name).parts
        base_name = Path(file_name).stem
        
        # If all files have the same name, use image_id to make them unique
        # Try to extract folder ID from path, otherwise use image_id
        if len(path_parts) > 1:
            # Try to get a unique part from the path (e.g., folder number)
            folder_id = path_parts[-2] if len(path_parts) >= 2 else str(image_id)
            unique_name = f"{folder_id}_{base_name}"
        else:
            unique_name = f"{image_id}_{base_name}"
        
        # Create YOLO label file
        label_file = output_dir / f"{unique_name}.txt"
        
        # Get annotations for this image
        img_annotations = annotations_by_image.get(image_id, [])
        
        if not img_annotations:
            # Create empty file if no annotations
            label_file.touch()
            continue
        
        # Write YOLO format annotations
        with open(label_file, 'w') as f:
            for ann in img_annotations:
                category_id = ann['category_id']
                bbox = ann['bbox']
                
                # Convert COCO bbox to YOLO format
                center_x, center_y, width_norm, height_norm = coco_bbox_to_yolo(
                    bbox, img_width, img_height
                )
                
                # YOLO format: class_id center_x center_y width height
                # Note: For room detection, we typically use class 0 for rooms
                # If you want to keep category IDs, use: category_id - 1 (YOLO uses 0-indexed)
                # For rooms only (category_id=2), this becomes class 0
                class_id = category_id - 1 if category_id > 0 else 0
                
                f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width_norm:.6f} {height_norm:.6f}\n")
        
        stats['converted_files'] += 1
    
    return stats

def main():
    """Main conversion function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert COCO format annotations to YOLO format'
    )
    parser.add_argument(
        '--coco-json',
        required=True,
        help='Path to COCO format JSON file (e.g., train_coco_pt.json)'
    )
    parser.add_argument(
        '--output-dir',
        required=True,
        help='Output directory for YOLO format label files'
    )
    parser.add_argument(
        '--rooms-only',
        action='store_true',
        help='Only convert room annotations (category_id=2), ignore walls'
    )
    
    args = parser.parse_args()
    
    # Set category filter if rooms-only
    category_filter = [2] if args.rooms_only else None
    
    print(f"Converting COCO annotations from: {args.coco_json}")
    print(f"Output directory: {args.output_dir}")
    if args.rooms_only:
        print("Filter: ROOMS ONLY (category_id=2)")
    print()
    
    stats = convert_coco_to_yolo(
        args.coco_json,
        args.output_dir,
        category_filter=category_filter
    )
    
    print("=" * 60)
    print("Conversion Statistics:")
    print(f"  Total images in COCO file: {stats['total_images']}")
    print(f"  Images with annotations: {stats['images_with_annotations']}")
    print(f"  Total annotations converted: {stats['total_annotations']}")
    print(f"  YOLO label files created: {stats['converted_files']}")
    print("=" * 60)
    print(f"\n✓ YOLO labels saved to: {args.output_dir}")

if __name__ == "__main__":
    main()

