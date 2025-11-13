#!/usr/bin/env python3
"""
Regenerate validation images without "Room X" labels.
Reads the validation report JSON files and regenerates all images with show_labels=False.
"""

import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

# Add parent directory to path to import from validate_annotations
sys.path.insert(0, str(Path(__file__).parent))
from validate_annotations import (
    load_yolo_label,
    visualize_annotations_on_image,
    find_image_file
)

def regenerate_validation_images(validation_report_path, dataset_root, yolo_labels_dir):
    """
    Regenerate validation images without labels based on validation report.
    
    Args:
        validation_report_path: Path to validation_report_{split}.json
        dataset_root: Root directory of the dataset
        yolo_labels_dir: Directory containing YOLO label files
    """
    # Load validation report
    with open(validation_report_path, 'r') as f:
        report = json.load(f)
    
    split = report['split']
    results = report['results']
    
    print(f"\n{'='*60}")
    print(f"Regenerating {split.upper()} validation images (without labels)")
    print(f"{'='*60}\n")
    
    yolo_labels_path = Path(yolo_labels_dir) / split
    output_dir = Path(validation_report_path).parent
    
    success_count = 0
    failed_count = 0
    
    for idx, result in enumerate(results, 1):
        if result['status'] != 'success':
            print(f"[{idx}/{len(results)}] ⚠️  Skipping failed sample: {result.get('sample_id', 'unknown')}")
            continue
        
        image_path = Path(result['image_path'])
        label_file = Path(result['label_file'])
        output_file = Path(result['output_file'])
        
        # Ensure label file path is correct
        if not label_file.is_absolute():
            label_file = yolo_labels_path / label_file.name
        
        # Load YOLO annotations
        yolo_annotations = load_yolo_label(label_file)
        
        if not yolo_annotations:
            print(f"[{idx}/{len(results)}] ⚠️  No annotations found: {label_file}")
            continue
        
        try:
            # Regenerate image without labels
            success = visualize_annotations_on_image(
                str(image_path),
                yolo_annotations,
                str(output_file),
                format='yolo',
                show_labels=False,  # This removes the "Room X" labels
                color_scheme='distinct'
            )
            
            if success:
                print(f"[{idx}/{len(results)}] ✓ Regenerated: {output_file.name}")
                success_count += 1
            else:
                print(f"[{idx}/{len(results)}] ❌ Failed to regenerate: {output_file.name}")
                failed_count += 1
                
        except Exception as e:
            print(f"[{idx}/{len(results)}] ❌ Error regenerating {output_file.name}: {e}")
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"Regeneration complete for {split.upper()} set!")
    print(f"  ✓ Successfully regenerated: {success_count} images")
    print(f"  ❌ Failed: {failed_count} images")
    print(f"{'='*60}\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Regenerate validation images without "Room X" labels'
    )
    parser.add_argument(
        '--validation-reports-dir',
        default='data/validation_samples',
        help='Directory containing validation_report_*.json files (default: data/validation_samples)'
    )
    parser.add_argument(
        '--dataset-root',
        required=True,
        help='Root directory of cubicasa5k dataset'
    )
    parser.add_argument(
        '--yolo-labels-dir',
        default='data/yolo_labels',
        help='Directory containing YOLO label files (default: data/yolo_labels)'
    )
    parser.add_argument(
        '--split',
        choices=['train', 'val', 'test', 'all'],
        default='all',
        help='Which split to regenerate: train, val, test, or all (default: all)'
    )
    
    args = parser.parse_args()
    
    validation_reports_dir = Path(args.validation_reports_dir)
    splits = ['train', 'val', 'test'] if args.split == 'all' else [args.split]
    
    for split in splits:
        report_path = validation_reports_dir / f"validation_report_{split}.json"
        if report_path.exists():
            regenerate_validation_images(
                report_path,
                args.dataset_root,
                args.yolo_labels_dir
            )
        else:
            print(f"⚠️  Validation report not found: {report_path}")

if __name__ == "__main__":
    main()

