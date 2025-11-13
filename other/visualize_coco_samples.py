#!/usr/bin/env python3
"""
Visualize COCO room annotations on images to verify training data quality.
Annotates 10 sample images with bounding boxes for review.
"""

import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

def find_image_file(image_path_from_coco, dataset_root):
    """
    Find the actual image file path from COCO annotation path.
    COCO paths are like: /kaggle/input/cubicasa5k/cubicasa5k/cubicasa5k/high_quality/1234/F1_original.png
    We need to extract the sample ID and find it locally.
    """
    # Extract sample ID from path
    # Path format: .../high_quality/1234/F1_original.png or .../high_quality_architectural/1234/F1_original.png
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
    
    local_path = Path(dataset_root) / folder_name / sample_id
    if local_path.exists():
        for name in possible_names:
            img_path = local_path / name
            if img_path.exists():
                return img_path
    
    return None

def visualize_coco_annotations(coco_json_path, dataset_root, output_dir, num_samples=10):
    """
    Visualize room annotations on sample images.
    
    Args:
        coco_json_path: Path to COCO JSON file
        dataset_root: Root directory of the cubicasa5k dataset
        output_dir: Directory to save annotated images
        num_samples: Number of sample images to visualize
    """
    # Load COCO data
    print(f"Loading COCO annotations from: {coco_json_path}")
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # Build mappings
    images = {img['id']: img for img in coco_data['images']}
    categories = {cat['id']: cat['name'] for cat in coco_data['categories']}
    
    # Get room annotations only
    room_annotations = [ann for ann in coco_data['annotations'] if ann['category_id'] == 2]
    
    # Group by image_id
    annotations_by_image = {}
    for ann in room_annotations:
        image_id = ann['image_id']
        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []
        annotations_by_image[image_id].append(ann)
    
    # Select random samples
    image_ids_with_rooms = list(annotations_by_image.keys())
    random.shuffle(image_ids_with_rooms)
    selected_ids = image_ids_with_rooms[:num_samples]
    
    print(f"\nFound {len(image_ids_with_rooms)} images with room annotations")
    print(f"Selecting {len(selected_ids)} random samples for visualization\n")
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each selected image
    success_count = 0
    failed_count = 0
    
    for idx, image_id in enumerate(selected_ids, 1):
        image_info = images[image_id]
        image_path_coco = image_info['file_name']
        
        # Find actual image file
        image_path = find_image_file(image_path_coco, dataset_root)
        
        if not image_path or not image_path.exists():
            print(f"[{idx}/{num_samples}] ❌ Could not find image: {image_path_coco}")
            failed_count += 1
            continue
        
        try:
            # Load image
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            
            # Get annotations for this image
            annotations = annotations_by_image[image_id]
            
            # Draw bounding boxes
            colors = [
                (255, 0, 0),    # Red
                (0, 255, 0),    # Green
                (0, 0, 255),    # Blue
                (255, 255, 0),  # Yellow
                (255, 0, 255),  # Magenta
                (0, 255, 255),  # Cyan
            ]
            
            for i, ann in enumerate(annotations):
                bbox = ann['bbox']  # [x, y, width, height]
                x, y, w, h = bbox
                
                # COCO format: top-left corner + width/height
                # PIL rectangle needs: [(x1, y1), (x2, y2)]
                x1, y1 = x, y
                x2, y2 = x + w, y + h
                
                # Choose color
                color = colors[i % len(colors)]
                
                # Draw rectangle (no labels)
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            
            # Save annotated image
            output_filename = f"sample_{idx:02d}_{Path(image_path).parent.name}_{Path(image_path).stem}_annotated.png"
            output_path = output_dir / output_filename
            img.save(output_path)
            
            print(f"[{idx}/{num_samples}] ✓ {Path(image_path).parent.name}/{Path(image_path).name}")
            print(f"    Rooms: {len(annotations)}, Size: {img.size[0]}x{img.size[1]}")
            success_count += 1
            
        except Exception as e:
            print(f"[{idx}/{num_samples}] ❌ Error processing {image_path}: {e}")
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"Visualization complete!")
    print(f"  ✓ Successfully annotated: {success_count} images")
    print(f"  ❌ Failed: {failed_count} images")
    print(f"  📁 Output directory: {output_dir}")
    print(f"{'='*60}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Visualize COCO room annotations on sample images'
    )
    parser.add_argument(
        '--coco-json',
        required=True,
        help='Path to COCO JSON file'
    )
    parser.add_argument(
        '--dataset-root',
        required=True,
        help='Root directory of cubicasa5k dataset'
    )
    parser.add_argument(
        '--output-dir',
        default='./annotated_samples',
        help='Output directory for annotated images (default: ./annotated_samples)'
    )
    parser.add_argument(
        '--num-samples',
        type=int,
        default=10,
        help='Number of samples to visualize (default: 10)'
    )
    
    args = parser.parse_args()
    
    visualize_coco_annotations(
        args.coco_json,
        args.dataset_root,
        args.output_dir,
        args.num_samples
    )

if __name__ == "__main__":
    main()

