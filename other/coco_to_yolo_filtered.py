#!/usr/bin/env python3
"""
Convert COCO format annotations to YOLO format with folder filtering.
Allows you to include/exclude specific folders (high_quality, high_quality_architectural, colorful).
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def coco_bbox_to_yolo(bbox, img_width, img_height):
    """Convert COCO bbox format to YOLO format."""
    x, y, w, h = bbox
    center_x = (x + w / 2.0) / img_width
    center_y = (y + h / 2.0) / img_height
    width_norm = w / img_width
    height_norm = h / img_height
    return center_x, center_y, width_norm, height_norm

def extract_folder_from_path(image_path):
    """Extract folder name from COCO image path."""
    parts = Path(image_path).parts
    for part in parts:
        if part in ['high_quality', 'high_quality_architectural', 'colorful']:
            return part
    return None

def convert_coco_to_yolo_filtered(
    coco_json_path, 
    output_dir, 
    category_filter=None,
    include_folders=None,
    exclude_folders=None
):
    """
    Convert COCO format annotations to YOLO format with folder filtering.
    
    Args:
        coco_json_path: Path to COCO format JSON file
        output_dir: Directory to save YOLO format .txt label files
        category_filter: List of category IDs to include (None = all categories)
        include_folders: List of folder names to include (None = all folders)
        exclude_folders: List of folder names to exclude (None = no exclusions)
    
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
    
    # Filter images by folder
    if include_folders or exclude_folders:
        filtered_image_ids = set()
        for img_id, img_info in images.items():
            folder = extract_folder_from_path(img_info['file_name'])
            if folder:
                if include_folders and folder not in include_folders:
                    continue
                if exclude_folders and folder in exclude_folders:
                    continue
                filtered_image_ids.add(img_id)
        images = {img_id: img for img_id, img in images.items() if img_id in filtered_image_ids}
        print(f"Filtered to {len(images)} images based on folder criteria")
    
    # Filter annotations by category if specified
    annotations = coco_data['annotations']
    if category_filter:
        annotations = [ann for ann in annotations if ann['category_id'] in category_filter]
    
    # Filter annotations to only include filtered images
    annotations = [ann for ann in annotations if ann['image_id'] in images]
    
    # Group annotations by image_id
    annotations_by_image = defaultdict(list)
    for ann in annotations:
        annotations_by_image[ann['image_id']].append(ann)
    
    # Convert each image's annotations to YOLO format
    stats = {
        'total_images': len(images),
        'images_with_annotations': len(annotations_by_image),
        'total_annotations': len(annotations),
        'converted_files': 0,
        'by_folder': defaultdict(int)
    }
    
    for image_id, image_info in images.items():
        img_width = image_info['width']
        img_height = image_info['height']
        file_name = image_info['file_name']
        
        # Track folder
        folder = extract_folder_from_path(file_name)
        if folder:
            stats['by_folder'][folder] += 1
        
        # Get base filename without extension
        base_name = Path(file_name).stem
        
        # Create YOLO label file
        label_file = output_dir / f"{base_name}.txt"
        
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
                # For rooms only (category_id=2), this becomes class 0
                class_id = category_id - 1 if category_id > 0 else 0
                
                f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width_norm:.6f} {height_norm:.6f}\n")
        
        stats['converted_files'] += 1
    
    return stats

def main():
    """Main conversion function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert COCO format annotations to YOLO format with folder filtering'
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
    parser.add_argument(
        '--include-folders',
        nargs='+',
        choices=['high_quality', 'high_quality_architectural', 'colorful'],
        help='Only include images from these folders'
    )
    parser.add_argument(
        '--exclude-folders',
        nargs='+',
        choices=['high_quality', 'high_quality_architectural', 'colorful'],
        help='Exclude images from these folders'
    )
    
    args = parser.parse_args()
    
    # Set category filter if rooms-only
    category_filter = [2] if args.rooms_only else None
    
    print(f"Converting COCO annotations from: {args.coco_json}")
    print(f"Output directory: {args.output_dir}")
    if args.rooms_only:
        print("Filter: ROOMS ONLY (category_id=2)")
    if args.include_folders:
        print(f"Include folders: {', '.join(args.include_folders)}")
    if args.exclude_folders:
        print(f"Exclude folders: {', '.join(args.exclude_folders)}")
    print()
    
    stats = convert_coco_to_yolo_filtered(
        args.coco_json,
        args.output_dir,
        category_filter=category_filter,
        include_folders=args.include_folders,
        exclude_folders=args.exclude_folders
    )
    
    print("=" * 60)
    print("Conversion Statistics:")
    print(f"  Total images processed: {stats['total_images']}")
    print(f"  Images with annotations: {stats['images_with_annotations']}")
    print(f"  Total annotations converted: {stats['total_annotations']}")
    print(f"  YOLO label files created: {stats['converted_files']}")
    if stats['by_folder']:
        print("\n  Images by folder:")
        for folder, count in sorted(stats['by_folder'].items()):
            print(f"    {folder}: {count}")
    print("=" * 60)
    print(f"\n✓ YOLO labels saved to: {args.output_dir}")

if __name__ == "__main__":
    main()

