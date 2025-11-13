#!/usr/bin/env python3
"""
Validate annotation quality by visualizing random samples from the dataset.
Supports both COCO and YOLO format annotations for comparison.

This script:
1. Randomly selects sample images from train/val/test sets
2. Visualizes bounding boxes on images
3. Saves annotated images for manual review
4. Generates a validation report
"""

import json
import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict
import argparse

def find_image_file(image_path_from_coco, dataset_root):
    """
    Find the actual image file path from COCO annotation path.
    COCO paths are like: /kaggle/input/cubicasa5k/cubicasa5k/cubicasa5k/high_quality/1234/F1_original.png
    We need to extract the folder name and sample ID and find it locally.
    
    The dataset_root should point to either:
    - /path/to/archive/cubicasa5k/cubicasa5k (preferred)
    - /path/to/archive (will auto-detect cubicasa5k/cubicasa5k)
    """
    parts = Path(image_path_from_coco).parts
    
    # Find the folder name (high_quality, high_quality_architectural, or colorful)
    folder_name = None
    sample_id = None
    
    for i, part in enumerate(parts):
        if part in ['high_quality', 'high_quality_architectural', 'colorful']:
            folder_name = part
            if i + 1 < len(parts):
                sample_id = parts[i + 1]
            break
    
    if not folder_name or not sample_id:
        return None
    
    # Try different image file names
    possible_names = ['F1_original.png', 'F1_scaled.png', 'model.png']
    
    # Build the local path: dataset_root/folder_name/sample_id/
    # Handle different dataset_root formats
    dataset_path = Path(dataset_root)
    
    # Check if we need to navigate to cubicasa5k/cubicasa5k
    # Try multiple path combinations
    path_attempts = [
        dataset_path,  # Direct path (e.g., /path/to/archive/cubicasa5k/cubicasa5k)
        dataset_path / 'cubicasa5k' / 'cubicasa5k',  # /path/to/archive/cubicasa5k/cubicasa5k
        dataset_path / 'cubicasa5k',  # /path/to/archive/cubicasa5k
    ]
    
    for attempt_path in path_attempts:
        if attempt_path.exists() and (attempt_path / folder_name).exists():
            local_path = attempt_path / folder_name / sample_id
            if local_path.exists():
                for name in possible_names:
                    img_path = local_path / name
                    if img_path.exists():
                        return img_path
    
    return None

def load_yolo_label(label_file_path):
    """
    Load YOLO format label file.
    Format: class_id center_x center_y width height (normalized 0-1)
    """
    annotations = []
    if not label_file_path.exists():
        return annotations
    
    with open(label_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                center_x = float(parts[1])
                center_y = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                annotations.append({
                    'class_id': class_id,
                    'center_x': center_x,
                    'center_y': center_y,
                    'width': width,
                    'height': height
                })
    return annotations

def yolo_to_coco_bbox(yolo_ann, img_width, img_height):
    """
    Convert YOLO format (normalized center_x, center_y, width, height) to COCO format (x, y, width, height).
    """
    center_x = yolo_ann['center_x'] * img_width
    center_y = yolo_ann['center_y'] * img_height
    width = yolo_ann['width'] * img_width
    height = yolo_ann['height'] * img_height
    
    # COCO format: top-left corner + width/height
    x = center_x - (width / 2)
    y = center_y - (height / 2)
    
    return [x, y, width, height]

def visualize_annotations_on_image(image_path, annotations, output_path, format='yolo', 
                                   show_labels=True, color_scheme='distinct'):
    """
    Visualize bounding boxes on an image.
    
    Args:
        image_path: Path to the image file
        annotations: List of annotations (YOLO or COCO format)
        output_path: Path to save annotated image
        format: 'yolo' or 'coco'
        show_labels: Whether to show class labels
        color_scheme: 'distinct' (different color per box) or 'single' (same color)
    """
    try:
        # Load image
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
        
        img_width, img_height = img.size
        
        # Color palette for distinct boxes
        colors = [
            (255, 0, 0),      # Red
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
            (255, 255, 0),    # Yellow
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Cyan
            (255, 165, 0),    # Orange
            (128, 0, 128),    # Purple
            (255, 192, 203),  # Pink
            (0, 128, 128),    # Teal
        ]
        
        # Draw bounding boxes
        for i, ann in enumerate(annotations):
            if format == 'yolo':
                # Convert YOLO to pixel coordinates
                bbox = yolo_to_coco_bbox(ann, img_width, img_height)
                x, y, w, h = bbox
                x1, y1 = int(x), int(y)
                x2, y2 = int(x + w), int(y + h)
                class_id = ann.get('class_id', 0)
            else:  # COCO format
                bbox = ann['bbox']
                x, y, w, h = bbox
                x1, y1 = int(x), int(y)
                x2, y2 = int(x + w), int(y + h)
                class_id = ann.get('category_id', 0)
            
            # Choose color
            if color_scheme == 'distinct':
                color = colors[i % len(colors)]
            else:
                color = (255, 0, 0)  # Red
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            
            # Add label if requested
            if show_labels:
                label = f"Room {i+1}" if format == 'yolo' else f"Class {class_id}"
                # Draw text background
                text_bbox = draw.textbbox((x1, y1 - 20), label, font=font)
                draw.rectangle(text_bbox, fill=color, outline=color)
                draw.text((x1, y1 - 20), label, fill="white", font=font)
        
        # Save annotated image
        img.save(output_path)
        return True
        
    except Exception as e:
        print(f"Error visualizing {image_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_yolo_annotations(yolo_labels_dir, image_paths_mapping, dataset_root, 
                            output_dir, num_samples=20, split='train'):
    """
    Validate YOLO format annotations by visualizing random samples.
    
    Args:
        yolo_labels_dir: Directory containing YOLO label files
        image_paths_mapping: Path to image_paths_mapping.json
        dataset_root: Root directory of the dataset
        output_dir: Directory to save validation samples
        num_samples: Number of samples to validate
        split: 'train', 'val', or 'test'
    """
    print(f"\n{'='*60}")
    print(f"Validating {split.upper()} annotations (YOLO format)")
    print(f"{'='*60}\n")
    
    # Load image paths mapping
    with open(image_paths_mapping, 'r') as f:
        mapping_data = json.load(f)
    
    # Get samples for the specified split
    split_samples = mapping_data.get(split, [])
    if not split_samples:
        print(f"❌ No samples found for split: {split}")
        return
    
    print(f"Found {len(split_samples)} samples in {split} set")
    
    # Randomly select samples
    random.shuffle(split_samples)
    selected_samples = split_samples[:num_samples]
    
    print(f"Selecting {len(selected_samples)} random samples for validation\n")
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each sample
    success_count = 0
    failed_count = 0
    validation_results = []
    
    yolo_labels_path = Path(yolo_labels_dir) / split
    
    for idx, sample in enumerate(selected_samples, 1):
        image_id = sample.get('image_id', idx)
        coco_image_path = sample.get('coco_image_path', '')
        yolo_label_file = sample.get('yolo_label_file', '')
        
        # Find the actual image file
        image_path = find_image_file(coco_image_path, dataset_root)
        
        if not image_path or not image_path.exists():
            print(f"[{idx}/{len(selected_samples)}] ❌ Could not find image: {coco_image_path}")
            failed_count += 1
            validation_results.append({
                'sample_id': image_id,
                'status': 'failed',
                'reason': 'Image not found'
            })
            continue
        
        # Load YOLO labels
        label_file_path = Path(yolo_label_file)
        if not label_file_path.is_absolute():
            label_file_path = yolo_labels_path / Path(yolo_label_file).name
        
        yolo_annotations = load_yolo_label(label_file_path)
        
        if not yolo_annotations:
            print(f"[{idx}/{len(selected_samples)}] ⚠️  No annotations found: {label_file_path}")
            # Still create visualization with empty annotations
        
        try:
            # Create output filename
            sample_folder = Path(image_path).parent.name
            sample_name = Path(image_path).stem
            output_filename = f"{split}_sample_{idx:02d}_{sample_folder}_{sample_name}_validated.png"
            output_path = output_dir / output_filename
            
            # Visualize
            success = visualize_annotations_on_image(
                image_path,
                yolo_annotations,
                output_path,
                format='yolo',
                show_labels=True,
                color_scheme='distinct'
            )
            
            if success:
                print(f"[{idx}/{len(selected_samples)}] ✓ {sample_folder}/{Path(image_path).name}")
                print(f"    Rooms: {len(yolo_annotations)}, Size: {Image.open(image_path).size[0]}x{Image.open(image_path).size[1]}")
                success_count += 1
                validation_results.append({
                    'sample_id': image_id,
                    'status': 'success',
                    'image_path': str(image_path),
                    'label_file': str(label_file_path),
                    'num_rooms': len(yolo_annotations),
                    'output_file': str(output_path)
                })
            else:
                failed_count += 1
                validation_results.append({
                    'sample_id': image_id,
                    'status': 'failed',
                    'reason': 'Visualization error'
                })
                
        except Exception as e:
            print(f"[{idx}/{len(selected_samples)}] ❌ Error processing {image_path}: {e}")
            failed_count += 1
            validation_results.append({
                'sample_id': image_id,
                'status': 'failed',
                'reason': str(e)
            })
    
    # Save validation report
    report_path = output_dir / f"validation_report_{split}.json"
    with open(report_path, 'w') as f:
        json.dump({
            'split': split,
            'total_samples': len(selected_samples),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': validation_results
        }, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Validation complete for {split.upper()} set!")
    print(f"  ✓ Successfully validated: {success_count} images")
    print(f"  ❌ Failed: {failed_count} images")
    print(f"  📁 Output directory: {output_dir}")
    print(f"  📄 Report saved: {report_path}")
    print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Validate annotation quality by visualizing random samples'
    )
    parser.add_argument(
        '--yolo-labels-dir',
        default='data/yolo_labels',
        help='Directory containing YOLO label files (default: data/yolo_labels)'
    )
    parser.add_argument(
        '--image-paths-mapping',
        default='data/image_paths_mapping.json',
        help='Path to image_paths_mapping.json (default: data/image_paths_mapping.json)'
    )
    parser.add_argument(
        '--dataset-root',
        required=True,
        help='Root directory of cubicasa5k dataset (e.g., /path/to/archive/cubicasa5k/cubicasa5k or /path/to/archive)'
    )
    parser.add_argument(
        '--output-dir',
        default='data/validation_samples',
        help='Output directory for validation samples (default: data/validation_samples)'
    )
    parser.add_argument(
        '--num-samples',
        type=int,
        default=20,
        help='Number of samples per split to validate (default: 20)'
    )
    parser.add_argument(
        '--split',
        choices=['train', 'val', 'test', 'all'],
        default='all',
        help='Which split to validate: train, val, test, or all (default: all)'
    )
    
    args = parser.parse_args()
    
    splits = ['train', 'val', 'test'] if args.split == 'all' else [args.split]
    
    for split in splits:
        validate_yolo_annotations(
            args.yolo_labels_dir,
            args.image_paths_mapping,
            args.dataset_root,
            args.output_dir,
            args.num_samples,
            split
        )

if __name__ == "__main__":
    main()

