#!/usr/bin/env python3
"""
Analyze COCO format annotations to understand the dataset structure.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter

def analyze_coco_file(coco_json_path):
    """Analyze a COCO format JSON file and print statistics."""
    
    with open(coco_json_path, 'r') as f:
        data = json.load(f)
    
    # Basic info
    print(f"\n{'='*60}")
    print(f"Analyzing: {Path(coco_json_path).name}")
    print(f"{'='*60}\n")
    
    # Categories
    categories = {cat['id']: cat['name'] for cat in data['categories']}
    print("Categories:")
    for cat_id, cat_name in sorted(categories.items()):
        print(f"  ID {cat_id}: {cat_name}")
    
    # Image statistics
    images = data['images']
    print(f"\nImages: {len(images)}")
    
    # Annotation statistics
    annotations = data['annotations']
    print(f"Total annotations: {len(annotations)}")
    
    # Count by category
    category_counts = Counter(ann['category_id'] for ann in annotations)
    print("\nAnnotations by category:")
    for cat_id, count in sorted(category_counts.items()):
        cat_name = categories.get(cat_id, 'Unknown')
        print(f"  {cat_name} (ID {cat_id}): {count}")
    
    # Images with annotations
    images_with_annos = set(ann['image_id'] for ann in annotations)
    print(f"\nImages with annotations: {len(images_with_annos)}")
    print(f"Images without annotations: {len(images) - len(images_with_annos)}")
    
    # Room-specific stats
    room_annotations = [ann for ann in annotations if ann['category_id'] == 2]
    if room_annotations:
        print(f"\nRoom annotations: {len(room_annotations)}")
        
        # Rooms per image
        rooms_per_image = defaultdict(int)
        for ann in room_annotations:
            rooms_per_image[ann['image_id']] += 1
        
        room_counts = list(rooms_per_image.values())
        if room_counts:
            print(f"  Average rooms per image: {sum(room_counts) / len(room_counts):.2f}")
            print(f"  Min rooms: {min(room_counts)}")
            print(f"  Max rooms: {max(room_counts)}")
        
        # Sample room annotation
        print("\nSample room annotation:")
        sample = room_annotations[0]
        print(f"  Image ID: {sample['image_id']}")
        print(f"  Bbox (COCO format): {sample['bbox']}  [x, y, width, height]")
        print(f"  Area: {sample['area']} pixels²")
    
    # Image dimensions
    if images:
        widths = [img['width'] for img in images]
        heights = [img['height'] for img in images]
        print(f"\nImage dimensions:")
        print(f"  Width range: {min(widths)} - {max(widths)}")
        print(f"  Height range: {min(heights)} - {max(heights)}")
        print(f"  Average: {sum(widths)/len(widths):.0f} x {sum(heights)/len(heights):.0f}")
    
    # File paths
    if images:
        print(f"\nSample image file paths:")
        for img in images[:3]:
            print(f"  {img['file_name']}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze COCO format annotations')
    parser.add_argument('coco_json', help='Path to COCO JSON file')
    
    args = parser.parse_args()
    
    analyze_coco_file(args.coco_json)

if __name__ == "__main__":
    main()

