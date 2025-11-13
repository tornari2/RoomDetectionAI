#!/usr/bin/env python3
"""
Create image paths mapping JSON file.
Maps COCO annotation image paths to YOLO label file paths.
"""

import json
import os
from pathlib import Path

def create_image_paths_mapping(coco_json_paths, yolo_label_dirs, output_file):
    """
    Create a mapping file that links COCO image paths to YOLO label files.
    
    Args:
        coco_json_paths: Dict mapping dataset name to COCO JSON file path
        yolo_label_dirs: Dict mapping dataset name to YOLO label directory
        output_file: Path to output JSON file
    """
    mapping = {
        "train": [],
        "val": [],
        "test": []
    }
    
    for dataset_name in ["train", "val", "test"]:
        coco_file = coco_json_paths[dataset_name]
        label_dir = Path(yolo_label_dirs[dataset_name])
        
        # Load COCO annotations
        with open(coco_file, 'r') as f:
            coco_data = json.load(f)
        
        # Build image mapping
        images = {img['id']: img for img in coco_data['images']}
        
        for image_id, image_info in images.items():
            file_name = image_info['file_name']
            
            # Extract unique identifier for YOLO label file
            path_parts = Path(file_name).parts
            base_name = Path(file_name).stem
            
            if len(path_parts) > 1:
                folder_id = path_parts[-2] if len(path_parts) >= 2 else str(image_id)
                unique_name = f"{folder_id}_{base_name}"
            else:
                unique_name = f"{image_id}_{base_name}"
            
            yolo_label_file = label_dir / f"{unique_name}.txt"
            
            mapping[dataset_name].append({
                "image_id": image_id,
                "coco_image_path": file_name,
                "yolo_label_file": str(yolo_label_file.relative_to(Path("data/yolo_labels").parent)),
                "image_width": image_info['width'],
                "image_height": image_info['height']
            })
    
    # Save mapping
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✓ Image paths mapping saved to: {output_file}")
    print(f"  Train mappings: {len(mapping['train'])}")
    print(f"  Val mappings: {len(mapping['val'])}")
    print(f"  Test mappings: {len(mapping['test'])}")

if __name__ == "__main__":
    coco_dir = "/Users/michaeltornaritis/Downloads/archive/cubicasa5k_coco"
    
    coco_json_paths = {
        "train": f"{coco_dir}/train_coco_pt.json",
        "val": f"{coco_dir}/val_coco_pt.json",
        "test": f"{coco_dir}/test_coco_pt.json"
    }
    
    yolo_label_dirs = {
        "train": "data/yolo_labels/train",
        "val": "data/yolo_labels/val",
        "test": "data/yolo_labels/test"
    }
    
    output_file = "data/image_paths_mapping.json"
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    create_image_paths_mapping(coco_json_paths, yolo_label_dirs, output_file)

