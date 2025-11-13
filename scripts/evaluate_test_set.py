#!/usr/bin/env python3
"""
Evaluate trained YOLOv8 model on test dataset with current inference thresholds.
Uses conf=0.25 and iou=0.45 as specified in inference.py
"""

import json
import yaml
import os
import shutil
import tempfile
from pathlib import Path
from ultralytics import YOLO
import boto3
from botocore.exceptions import ClientError

# Configuration
MODEL_PATH = "sagemaker/outputs/model_artifacts/yolov8-room-detection-20251108-224902/model.pt"
CONF_THRESHOLD = 0.25  # Current inference threshold
IOU_THRESHOLD = 0.45   # Current NMS threshold
S3_BUCKET = "room-detection-ai-blueprints-dev"
S3_REGION = "us-east-2"
S3_TEST_PREFIX = "training/test"

def find_local_test_images(mapping_file, dataset_root_candidates):
    """Try to find test images locally."""
    # First check the most likely location based on the test.txt file
    likely_path = Path("data/archive/cubicasa5k/cubicasa5k")
    if likely_path.exists():
        # Verify by checking a test image
        test_image_path = likely_path / "high_quality_architectural" / "1191" / "F1_original.png"
        if test_image_path.exists():
            print(f"✓ Found test images in: {likely_path}")
            return str(likely_path)
    
    # Fallback to checking other locations
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    
    test_samples = mapping.get('test', [])[:5]  # Check first 5 samples
    
    for dataset_root in dataset_root_candidates:
        dataset_path = Path(dataset_root)
        if not dataset_path.exists():
            continue
            
        found_count = 0
        for sample in test_samples:
            coco_path = sample['coco_image_path']
            # Extract folder and sample_id from path like:
            # /kaggle/input/cubicasa5k/cubicasa5k/cubicasa5k/high_quality_architectural/1191/F1_original.png
            parts = Path(coco_path).parts
            folder_name = None
            sample_id = None
            
            for i, part in enumerate(parts):
                if part in ['high_quality', 'high_quality_architectural', 'colorful']:
                    folder_name = part
                    if i + 1 < len(parts):
                        sample_id = parts[i + 1]
                    break
            
            if folder_name and sample_id:
                # Try different path structures
                for attempt in [
                    dataset_path / folder_name / sample_id / 'F1_original.png',
                    dataset_path / 'cubicasa5k' / 'cubicasa5k' / folder_name / sample_id / 'F1_original.png',
                ]:
                    if attempt.exists():
                        found_count += 1
                        break
        
        if found_count > 0:
            print(f"✓ Found test images in: {dataset_path}")
            return str(dataset_path)
    
    return None

def download_test_images_from_s3(temp_dir, max_images=None):
    """Download test images from S3 to temporary directory."""
    print(f"Attempting to download test images from S3...")
    print(f"  Bucket: {S3_BUCKET}")
    print(f"  Prefix: {S3_TEST_PREFIX}")
    
    s3_client = boto3.client('s3', region_name=S3_REGION)
    
    try:
        # List objects in test/images/
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=f"{S3_TEST_PREFIX}/images/",
            MaxKeys=1000
        )
        
        if 'Contents' not in response:
            print("  ⚠️  No test images found in S3")
            return None
        
        images = response['Contents']
        if max_images:
            images = images[:max_images]
        
        print(f"  Found {len(images)} test images in S3")
        
        # Create directory structure
        images_dir = Path(temp_dir) / 'images'
        labels_dir = Path(temp_dir) / 'labels'
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        # Download images
        downloaded = 0
        for obj in images:
            key = obj['Key']
            filename = Path(key).name
            local_path = images_dir / filename
            
            try:
                s3_client.download_file(S3_BUCKET, key, str(local_path))
                downloaded += 1
                if downloaded % 50 == 0:
                    print(f"  Downloaded {downloaded}/{len(images)} images...")
            except Exception as e:
                print(f"  ⚠️  Failed to download {filename}: {e}")
        
        print(f"  ✓ Downloaded {downloaded} images")
        
        # Download labels
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=f"{S3_TEST_PREFIX}/labels/",
            MaxKeys=1000
        )
        
        if 'Contents' in response:
            labels = response['Contents']
            downloaded_labels = 0
            for obj in labels:
                key = obj['Key']
                filename = Path(key).name
                local_path = labels_dir / filename
                
                try:
                    s3_client.download_file(S3_BUCKET, key, str(local_path))
                    downloaded_labels += 1
                except Exception as e:
                    print(f"  ⚠️  Failed to download label {filename}: {e}")
            
            print(f"  ✓ Downloaded {downloaded_labels} label files")
        
        return str(temp_dir)
        
    except ClientError as e:
        print(f"  ❌ Error accessing S3: {e}")
        return None

def setup_test_dataset(test_data_dir, output_yaml):
    """Set up YOLOv8 dataset structure and create YAML."""
    test_path = Path(test_data_dir)
    
    # Check if we have images and labels
    images_dir = test_path / 'images'
    labels_dir = test_path / 'labels'
    
    # If structure is different, try to find them
    if not images_dir.exists():
        # Maybe labels are in yolo_labels/test/
        labels_dir = Path('data/yolo_labels/test')
        if labels_dir.exists():
            # We need to create images directory structure
            images_dir = test_path / 'images'
            images_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dataset YAML
    dataset_config = {
        'path': str(test_path.absolute()),
        'test': '.',  # Current directory should have images/ and labels/
        'nc': 1,
        'names': ['room']
    }
    
    with open(output_yaml, 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)
    
    return output_yaml

def evaluate_on_test_set():
    """Evaluate model on test set with current thresholds."""
    print("=" * 80)
    print("Evaluating Model on Test Set")
    print("=" * 80)
    print(f"\nModel: {MODEL_PATH}")
    print(f"Confidence Threshold: {CONF_THRESHOLD}")
    print(f"IoU Threshold: {IOU_THRESHOLD}")
    print()
    
    # Check if model exists
    if not Path(MODEL_PATH).exists():
        print(f"❌ Model not found: {MODEL_PATH}")
        return None
    
    # Load model
    print("Loading model...")
    model = YOLO(MODEL_PATH)
    print("✓ Model loaded")
    
    # Try to find test images
    print("\nLooking for test images...")
    
    # Check local locations (prioritize the local archive)
    dataset_root_candidates = [
        "data/archive/cubicasa5k/cubicasa5k",  # Most likely location
        "/Users/michaeltornaritis/Downloads/archive/cubicasa5k/cubicasa5k",
        "/Users/michaeltornaritis/Downloads/archive",
        "data",
    ]
    
    local_dataset = find_local_test_images("data/image_paths_mapping.json", dataset_root_candidates)
    
    test_data_dir = None
    temp_dir = None
    
    if local_dataset:
        print(f"✓ Using local dataset: {local_dataset}")
        # We'll need to set up the structure properly
        # For now, use labels from data/yolo_labels/test
        test_data_dir = "data"
    else:
        print("  Local images not found, trying S3...")
        # Try downloading from S3
        temp_dir = tempfile.mkdtemp(prefix="test_eval_")
        s3_dataset = download_test_images_from_s3(temp_dir)
        
        if s3_dataset:
            test_data_dir = s3_dataset
        else:
            print("\n❌ Could not find test images locally or on S3")
            print("\nTo evaluate on test set, you need:")
            print("1. Test images in a local directory, OR")
            print("2. Test images uploaded to S3 at s3://{}/{}".format(S3_BUCKET, S3_TEST_PREFIX))
            print("\nYou can:")
            print("- Set DATASET_ROOT environment variable to point to your cubicasa5k dataset")
            print("- Or upload test images to S3 using the upload script")
            return None
    
    # Set up dataset structure for YOLOv8
    # YOLOv8 expects: dataset_root/images/ and dataset_root/labels/
    # We have labels in data/yolo_labels/test/ and images in the dataset root
    
    # Create a temporary structure with proper YOLOv8 format
    eval_temp_dir = tempfile.mkdtemp(prefix="yolo_test_")
    eval_images = Path(eval_temp_dir) / 'images'
    eval_labels = Path(eval_temp_dir) / 'labels'
    eval_images.mkdir(parents=True, exist_ok=True)
    eval_labels.mkdir(parents=True, exist_ok=True)
    
    # Copy labels from data/yolo_labels/test/
    source_labels = Path("data/yolo_labels/test")
    if source_labels.exists():
        label_count = 0
        for label_file in source_labels.glob("*.txt"):
            shutil.copy2(label_file, eval_labels / label_file.name)
            label_count += 1
        print(f"✓ Copied {label_count} label files")
    else:
        print("❌ Test labels not found in data/yolo_labels/test/")
        shutil.rmtree(eval_temp_dir)
        return None
    
    # Copy or symlink images from dataset
    # test_data_dir is the local dataset path (e.g., "data/archive/cubicasa5k/cubicasa5k")
    dataset_path = Path(local_dataset) if local_dataset else Path(test_data_dir)
    mapping_file = Path("data/image_paths_mapping.json")
    
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    
    test_samples = mapping.get('test', [])
    image_count = 0
    
    print(f"Copying test images from dataset: {dataset_path}")
    for sample in test_samples:
        coco_path = sample['coco_image_path']
        label_file_name = Path(sample['yolo_label_file']).name
        
        # Extract folder and sample_id from COCO path
        parts = Path(coco_path).parts
        folder_name = None
        sample_id = None
        
        for i, part in enumerate(parts):
            if part in ['high_quality', 'high_quality_architectural', 'colorful']:
                folder_name = part
                if i + 1 < len(parts):
                    sample_id = parts[i + 1]
                break
        
        if folder_name and sample_id:
            # Find the image file
            image_path = dataset_path / folder_name / sample_id / 'F1_original.png'
            if image_path.exists():
                # Copy image with same name as label (but .png extension)
                image_name = label_file_name.replace('.txt', '.png')
                shutil.copy2(image_path, eval_images / image_name)
                image_count += 1
                if image_count % 50 == 0:
                    print(f"  Copied {image_count}/{len(test_samples)} images...")
            elif image_count < 3:  # Debug first few failures
                print(f"  ⚠️  Image not found: {image_path}")
    
    print(f"✓ Copied {image_count} test images")
    
    if image_count == 0:
        print("❌ No test images found. Cannot run evaluation.")
        shutil.rmtree(eval_temp_dir)
        return None
    
    test_data_dir = eval_temp_dir
    
    # Create dataset YAML
    # YOLOv8 requires 'train' and 'val' keys even for test evaluation
    dataset_yaml = Path("test_dataset_temp.yaml")
    dataset_config = {
        'path': str(Path(test_data_dir).absolute()),
        'train': 'images',  # Required by YOLOv8 (won't be used for test eval)
        'val': 'images',    # Required by YOLOv8 (won't be used for test eval)
        'test': 'images',   # This is what we'll actually evaluate
        'nc': 1,
        'names': ['room']
    }
    
    with open(dataset_yaml, 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)
    
    print(f"\nDataset YAML created: {dataset_yaml}")
    print(f"Test data directory: {test_data_dir}")
    print(f"  Images: {len(list(Path(test_data_dir).glob('images/*.png')))} files")
    print(f"  Labels: {len(list(Path(test_data_dir).glob('labels/*.txt')))} files")
    
    # Check if we have the required structure
    test_path = Path(test_data_dir)
    if not (test_path / 'labels').exists() or len(list((test_path / 'labels').glob('*.txt'))) == 0:
        print("❌ No label files found in test directory")
        if eval_temp_dir:
            shutil.rmtree(eval_temp_dir)
        if temp_dir:
            shutil.rmtree(temp_dir)
        dataset_yaml.unlink()
        return None
    
    if not (test_path / 'images').exists() or len(list((test_path / 'images').glob('*.png'))) == 0:
        print("❌ No image files found in test directory")
        if eval_temp_dir:
            shutil.rmtree(eval_temp_dir)
        if temp_dir:
            shutil.rmtree(temp_dir)
        dataset_yaml.unlink()
        return None
    
    print(f"\nRunning evaluation on test set...")
    print("This may take several minutes...\n")
    
    try:
        # Run validation with current thresholds
        # Note: YOLOv8's val() requires images to be present
        # If images aren't available, this will fail
        # Use split='test' to evaluate on test set
        results = model.val(
            data=str(dataset_yaml),
            conf=CONF_THRESHOLD,
            iou=IOU_THRESHOLD,
            imgsz=640,
            split='test',  # Evaluate on test split
            save_json=True,
            plots=True
        )
        
        # Extract metrics
        metrics = {
            'conf_threshold': CONF_THRESHOLD,
            'iou_threshold': IOU_THRESHOLD,
            'test_metrics': {
                'mAP50': float(results.box.map50),
                'mAP50-95': float(results.box.map),
                'precision': float(results.box.mp),
                'recall': float(results.box.mr),
            }
        }
        
        # Print results
        print("\n" + "=" * 80)
        print("Test Set Evaluation Results")
        print("=" * 80)
        print(f"\nConfidence Threshold: {CONF_THRESHOLD}")
        print(f"IoU Threshold: {IOU_THRESHOLD}")
        print(f"\nMetrics:")
        print(f"  mAP@0.5:     {metrics['test_metrics']['mAP50']:.4f} ({metrics['test_metrics']['mAP50']*100:.2f}%)")
        print(f"  mAP@0.5:0.95: {metrics['test_metrics']['mAP50-95']:.4f} ({metrics['test_metrics']['mAP50-95']*100:.2f}%)")
        print(f"  Precision:   {metrics['test_metrics']['precision']:.4f} ({metrics['test_metrics']['precision']*100:.2f}%)")
        print(f"  Recall:      {metrics['test_metrics']['recall']:.4f} ({metrics['test_metrics']['recall']*100:.2f}%)")
        
        # Compare with validation metrics
        val_metrics_path = Path("sagemaker/outputs/model_artifacts/yolov8-room-detection-20251108-224902/training_metrics.json")
        if val_metrics_path.exists():
            with open(val_metrics_path, 'r') as f:
                val_metrics = json.load(f)
            
            val_final = val_metrics.get('final_metrics', {})
            print(f"\n" + "=" * 80)
            print("Comparison: Validation vs Test")
            print("=" * 80)
            print(f"\n{'Metric':<20} {'Validation':<15} {'Test':<15} {'Difference':<15}")
            print("-" * 65)
            
            val_map50 = val_final.get('metrics/mAP50(B)', 0)
            test_map50 = metrics['test_metrics']['mAP50']
            diff_map50 = test_map50 - val_map50
            print(f"{'mAP@0.5':<20} {val_map50:<15.4f} {test_map50:<15.4f} {diff_map50:+.4f}")
            
            val_map50_95 = val_final.get('metrics/mAP50-95(B)', 0)
            test_map50_95 = metrics['test_metrics']['mAP50-95']
            diff_map50_95 = test_map50_95 - val_map50_95
            print(f"{'mAP@0.5:0.95':<20} {val_map50_95:<15.4f} {test_map50_95:<15.4f} {diff_map50_95:+.4f}")
            
            val_precision = val_final.get('metrics/precision(B)', 0)
            test_precision = metrics['test_metrics']['precision']
            diff_precision = test_precision - val_precision
            print(f"{'Precision':<20} {val_precision:<15.4f} {test_precision:<15.4f} {diff_precision:+.4f}")
            
            val_recall = val_final.get('metrics/recall(B)', 0)
            test_recall = metrics['test_metrics']['recall']
            diff_recall = test_recall - val_recall
            print(f"{'Recall':<20} {val_recall:<15.4f} {test_recall:<15.4f} {diff_recall:+.4f}")
            
            # Interpretation
            print(f"\n" + "=" * 80)
            print("Interpretation")
            print("=" * 80)
            if abs(diff_map50) < 0.02:
                print("✓ Test performance is very close to validation (good generalization)")
            elif diff_map50 < -0.05:
                print("⚠️  Test performance is lower than validation (possible overfitting)")
            else:
                print("✓ Test performance is better than validation (excellent!)")
        
        # Save results
        output_path = Path("sagemaker/outputs/test_evaluation_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")
        print("=" * 80)
        
        return metrics
        
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        print("\nThis might be because:")
        print("1. Test images are not accessible")
        print("2. Dataset structure doesn't match YOLOv8's expected format")
        print("3. Images need to be downloaded from S3 or located locally")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Cleanup
        if 'dataset_yaml' in locals() and dataset_yaml.exists():
            dataset_yaml.unlink()
        if 'eval_temp_dir' in locals() and eval_temp_dir and Path(eval_temp_dir).exists():
            shutil.rmtree(eval_temp_dir)
        if 'temp_dir' in locals() and temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    evaluate_on_test_set()

