#!/usr/bin/env python3
"""
Clean up YOLO label files by removing empty files (images without annotations)
and create a report of which images were annotated.
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def analyze_and_clean_labels(coco_json_paths, yolo_label_dirs, output_report_file):
    """
    Analyze annotations, remove empty label files, and create a report.
    
    Args:
        coco_json_paths: Dict mapping dataset name to COCO JSON file path
        yolo_label_dirs: Dict mapping dataset name to YOLO label directory
        output_report_file: Path to output report JSON file
    """
    report = {
        "summary": {},
        "images_annotated": {},
        "images_without_annotations": {},
        "image_type": "original",  # All images are F1_original.png
        "duplicate_analysis": {}
    }
    
    total_removed = 0
    
    for dataset_name in ["train", "val", "test"]:
        coco_file = coco_json_paths[dataset_name]
        label_dir = Path(yolo_label_dirs[dataset_name])
        
        # Load COCO annotations
        with open(coco_file, 'r') as f:
            coco_data = json.load(f)
        
        # Filter for room annotations only (category_id=2)
        room_annotations = [ann for ann in coco_data['annotations'] if ann['category_id'] == 2]
        images_with_rooms = set(ann['image_id'] for ann in room_annotations)
        
        # Build image mapping
        images = {img['id']: img for img in coco_data['images']}
        
        # Find images without room annotations
        images_without_rooms = [img for img_id, img in images.items() if img_id not in images_with_rooms]
        
        # Remove empty label files
        removed_files = []
        for img in images_without_rooms:
            file_name = img['file_name']
            path_parts = Path(file_name).parts
            base_name = Path(file_name).stem
            
            if len(path_parts) > 1:
                folder_id = path_parts[-2] if len(path_parts) >= 2 else str(img['id'])
                unique_name = f"{folder_id}_{base_name}"
            else:
                unique_name = f"{img['id']}_{base_name}"
            
            label_file = label_dir / f"{unique_name}.txt"
            if label_file.exists() and label_file.stat().st_size == 0:
                label_file.unlink()
                removed_files.append({
                    "image_id": img['id'],
                    "coco_image_path": file_name,
                    "label_file": str(label_file.name)
                })
                total_removed += 1
        
        # Build list of annotated images
        annotated_images = []
        for img_id in images_with_rooms:
            img = images[img_id]
            file_name = img['file_name']
            path_parts = Path(file_name).parts
            base_name = Path(file_name).stem
            
            if len(path_parts) > 1:
                folder_id = path_parts[-2] if len(path_parts) >= 2 else str(img_id)
                unique_name = f"{folder_id}_{base_name}"
            else:
                unique_name = f"{img_id}_{base_name}"
            
            # Count annotations for this image
            ann_count = len([ann for ann in room_annotations if ann['image_id'] == img_id])
            
            annotated_images.append({
                "image_id": img_id,
                "coco_image_path": file_name,
                "folder_id": path_parts[-2] if len(path_parts) > 1 else None,
                "filename": path_parts[-1] if path_parts else file_name,
                "yolo_label_file": f"{unique_name}.txt",
                "annotation_count": ann_count,
                "image_width": img['width'],
                "image_height": img['height']
            })
        
        # Check for duplicate folder IDs (same folder appearing multiple times)
        folder_to_images = defaultdict(list)
        for img in images.values():
            path_parts = img['file_name'].split('/')
            if len(path_parts) > 1:
                folder_id = path_parts[-2]
                folder_to_images[folder_id].append({
                    "image_id": img['id'],
                    "filename": path_parts[-1],
                    "full_path": img['file_name']
                })
        
        duplicate_folders = {k: v for k, v in folder_to_images.items() if len(v) > 1}
        
        report["summary"][dataset_name] = {
            "total_images": len(images),
            "images_with_annotations": len(images_with_rooms),
            "images_without_annotations": len(images_without_rooms),
            "empty_label_files_removed": len(removed_files),
            "total_room_annotations": len(room_annotations)
        }
        
        report["images_annotated"][dataset_name] = annotated_images
        report["images_without_annotations"][dataset_name] = [
            {
                "image_id": img['id'],
                "coco_image_path": img['file_name'],
                "folder_id": img['file_name'].split('/')[-2] if len(img['file_name'].split('/')) > 1 else None,
                "filename": img['file_name'].split('/')[-1]
            }
            for img in images_without_rooms
        ]
        
        report["duplicate_analysis"][dataset_name] = {
            "unique_folders": len(folder_to_images),
            "folders_with_multiple_images": len(duplicate_folders),
            "duplicate_folders": [
                {
                    "folder_id": folder_id,
                    "image_count": len(images),
                    "images": images[:5]  # Limit to first 5
                }
                for folder_id, images in list(duplicate_folders.items())[:10]
            ]
        }
    
    # Determine image type
    sample_image = list(report["images_annotated"]["train"])[0] if report["images_annotated"]["train"] else None
    if sample_image:
        filename = sample_image["filename"]
        if "F1_original" in filename:
            report["image_type"] = "original"
        elif "resized" in filename.lower() or "F1_resized" in filename:
            report["image_type"] = "resized"
        else:
            report["image_type"] = "unknown"
    
    # Save report
    with open(output_report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print("=" * 60)
    print("Annotation Analysis Report")
    print("=" * 60)
    print(f"\nImage Type: {report['image_type']}")
    print(f"\nTotal empty label files removed: {total_removed}")
    print("\nSummary by dataset:")
    for dataset, summary in report["summary"].items():
        print(f"\n{dataset.upper()}:")
        print(f"  Total images: {summary['total_images']}")
        print(f"  Images with annotations: {summary['images_with_annotations']}")
        print(f"  Images without annotations: {summary['images_without_annotations']}")
        print(f"  Empty files removed: {summary['empty_label_files_removed']}")
        print(f"  Total room annotations: {summary['total_room_annotations']}")
    
    print(f"\n✓ Report saved to: {output_report_file}")
    return report

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
    
    output_report_file = "data/annotation_report.json"
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(output_report_file), exist_ok=True)
    
    analyze_and_clean_labels(coco_json_paths, yolo_label_dirs, output_report_file)

