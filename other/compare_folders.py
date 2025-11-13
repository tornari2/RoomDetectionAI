#!/usr/bin/env python3
"""
Compare samples from different folders (high_quality, high_quality_architectural, colorful)
to help decide which folders to use for training.
"""

import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict
import random

def find_image_file(image_path_from_coco, dataset_root):
    """Find the actual image file path from COCO annotation path."""
    parts = Path(image_path_from_coco).parts
    
    folder_name = None
    sample_id = None
    
    for i, part in enumerate(parts):
        if part in ['high_quality', 'high_quality_architectural', 'colorful']:
            folder_name = part
            if i + 1 < len(parts):
                sample_id = parts[i + 1]
            break
    
    if not folder_name or not sample_id:
        return None, None
    
    possible_names = ['F1_original.png', 'F1_scaled.png', 'model.png']
    local_path = Path(dataset_root) / folder_name / sample_id
    
    if local_path.exists():
        for name in possible_names:
            img_path = local_path / name
            if img_path.exists():
                return img_path, folder_name
    
    return None, None

def analyze_image_characteristics(img_path):
    """Analyze image characteristics (color, brightness, etc.)."""
    try:
        img = Image.open(img_path)
        
        # Convert to RGB for analysis
        if img.mode != 'RGB':
            img_rgb = img.convert('RGB')
        else:
            img_rgb = img
        
        import numpy as np
        img_array = np.array(img_rgb)
        
        # Calculate color variance (low = grayscale, high = colorful)
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        color_variance = np.std([r, g, b])
        
        # Mean brightness
        mean_brightness = np.mean(img_array)
        
        # Check if mostly grayscale
        is_grayscale = color_variance < 30
        
        # Count unique colors (approximate)
        unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[-1]), axis=0))
        
        return {
            'is_grayscale': is_grayscale,
            'color_variance': float(color_variance),
            'mean_brightness': float(mean_brightness),
            'unique_colors': int(unique_colors),
            'size': img.size,
            'mode': img.mode
        }
    except Exception as e:
        return {'error': str(e)}

def visualize_folder_samples(coco_json_path, dataset_root, output_dir, samples_per_folder=5):
    """Visualize samples from each folder for comparison."""
    
    # Load COCO data
    print(f"Loading COCO annotations from: {coco_json_path}")
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # Build mappings
    images = {img['id']: img for img in coco_data['images']}
    
    # Get room annotations
    room_annotations = [ann for ann in coco_data['annotations'] if ann['category_id'] == 2]
    
    # Group by image_id
    annotations_by_image = defaultdict(list)
    for ann in room_annotations:
        annotations_by_image[ann['image_id']].append(ann)
    
    # Group images by folder
    images_by_folder = defaultdict(list)
    for image_id, image_info in images.items():
        img_path, folder_name = find_image_file(image_info['file_name'], dataset_root)
        if img_path and folder_name:
            images_by_folder[folder_name].append((image_id, image_info, img_path))
    
    print(f"\nFound images by folder:")
    for folder, img_list in images_by_folder.items():
        print(f"  {folder}: {len(img_list)} images")
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process samples from each folder
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
    
    folder_stats = {}
    
    for folder_name in ['high_quality', 'high_quality_architectural', 'colorful']:
        if folder_name not in images_by_folder:
            print(f"\n⚠️  No images found for folder: {folder_name}")
            continue
        
        print(f"\n{'='*60}")
        print(f"Processing folder: {folder_name}")
        print(f"{'='*60}")
        
        folder_images = images_by_folder[folder_name]
        random.shuffle(folder_images)
        selected = folder_images[:samples_per_folder]
        
        folder_stats[folder_name] = {
            'total': len(folder_images),
            'samples': []
        }
        
        for idx, (image_id, image_info, img_path) in enumerate(selected, 1):
            try:
                # Load image
                img = Image.open(img_path)
                draw = ImageDraw.Draw(img)
                
                # Analyze characteristics
                characteristics = analyze_image_characteristics(img_path)
                
                # Get annotations
                annotations = annotations_by_image.get(image_id, [])
                
                # Draw bounding boxes (no labels)
                for i, ann in enumerate(annotations):
                    bbox = ann['bbox']
                    x, y, w, h = bbox
                    x1, y1 = x, y
                    x2, y2 = x + w, y + h
                    
                    color = colors[i % len(colors)]
                    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                
                # Save annotated image
                output_filename = f"{folder_name}_sample_{idx:02d}_{Path(img_path).parent.name}_annotated.png"
                output_path = output_dir / output_filename
                img.save(output_path)
                
                # Store stats
                stats = {
                    'sample_id': Path(img_path).parent.name,
                    'rooms': len(annotations),
                    'size': img.size,
                    'characteristics': characteristics
                }
                folder_stats[folder_name]['samples'].append(stats)
                
                print(f"  [{idx}/{samples_per_folder}] ✓ {Path(img_path).parent.name}")
                print(f"      Rooms: {len(annotations)}, Size: {img.size[0]}x{img.size[1]}")
                if 'error' not in characteristics:
                    print(f"      Grayscale: {characteristics['is_grayscale']}, "
                          f"Color Variance: {characteristics['color_variance']:.1f}, "
                          f"Brightness: {characteristics['mean_brightness']:.1f}")
                
            except Exception as e:
                print(f"  [{idx}/{samples_per_folder}] ❌ Error: {e}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY BY FOLDER")
    print(f"{'='*60}\n")
    
    for folder_name, stats in folder_stats.items():
        print(f"{folder_name.upper()}:")
        print(f"  Total images: {stats['total']}")
        print(f"  Sample characteristics:")
        
        if stats['samples']:
            avg_rooms = sum(s['rooms'] for s in stats['samples']) / len(stats['samples'])
            print(f"    Average rooms per image: {avg_rooms:.1f}")
            
            grayscale_count = sum(1 for s in stats['samples'] 
                                if 'characteristics' in s and s['characteristics'].get('is_grayscale', False))
            print(f"    Grayscale samples: {grayscale_count}/{len(stats['samples'])}")
            
            if stats['samples']:
                sample = stats['samples'][0]
                if 'characteristics' in sample and 'error' not in sample['characteristics']:
                    char = sample['characteristics']
                    print(f"    Avg color variance: {char['color_variance']:.1f}")
                    print(f"    Avg brightness: {char['mean_brightness']:.1f}")
        print()
    
    print(f"📁 Annotated samples saved to: {output_dir}")
    print(f"\n💡 Review the annotated images to decide which folders to use for training.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Compare samples from different dataset folders'
    )
    parser.add_argument(
        '--coco-json',
        default='/Users/michaeltornaritis/Downloads/archive/cubicasa5k_coco/train_coco_pt.json',
        help='Path to COCO JSON file'
    )
    parser.add_argument(
        '--dataset-root',
        default='/Users/michaeltornaritis/Downloads/archive/cubicasa5k/cubicasa5k',
        help='Root directory of cubicasa5k dataset'
    )
    parser.add_argument(
        '--output-dir',
        default='./folder_comparison',
        help='Output directory for annotated images'
    )
    parser.add_argument(
        '--samples-per-folder',
        type=int,
        default=5,
        help='Number of samples to visualize per folder (default: 5)'
    )
    
    args = parser.parse_args()
    
    visualize_folder_samples(
        args.coco_json,
        args.dataset_root,
        args.output_dir,
        args.samples_per_folder
    )

