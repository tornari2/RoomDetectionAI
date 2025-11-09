#!/usr/bin/env python3
"""
Advanced SageMaker training script for YOLOv8 room detection model.
Includes comprehensive hyperparameter tuning, data augmentation, and optimization techniques.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import torch
from ultralytics import YOLO
import yaml


def parse_args():
    """Parse command line arguments with comprehensive hyperparameters."""
    parser = argparse.ArgumentParser(description='Advanced YOLOv8 Training with Hyperparameter Tuning')
    
    # Helper function to parse boolean values from strings (for SageMaker compatibility)
    def str2bool(v):
        """Convert string to boolean for argparse."""
        if isinstance(v, bool):
            return v
        if v.lower() in ('true', 't', '1'):
            return True
        elif v.lower() in ('false', 'f', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')
    
    # SageMaker environment variables
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR', '/opt/ml/model'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAINING', '/opt/ml/input/data/training'))
    parser.add_argument('--val-dir', type=str, default=os.environ.get('SM_CHANNEL_VALIDATION', '/opt/ml/input/data/validation'))
    parser.add_argument('--output-dir', type=str, default=os.environ.get('SM_OUTPUT_DATA_DIR', '/opt/ml/output'))
    
    # Basic hyperparameters
    parser.add_argument('--epochs', type=int, default=300)
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--img_size', type=int, default=640)
    parser.add_argument('--model_size', type=str, default='yolov8s.pt',
                       choices=['yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt'])
    
    # Learning rate and optimization
    parser.add_argument('--lr0', type=float, default=0.01, help='Initial learning rate')
    parser.add_argument('--lrf', type=float, default=0.01, help='Final learning rate (lr0 * lrf)')
    parser.add_argument('--momentum', type=float, default=0.937, help='SGD momentum/Adam beta1')
    parser.add_argument('--weight_decay', type=float, default=0.0005, help='Weight decay (L2 regularization)')
    parser.add_argument('--warmup_epochs', type=int, default=3, help='Warmup epochs')
    parser.add_argument('--warmup_momentum', type=float, default=0.8, help='Warmup initial momentum')
    parser.add_argument('--warmup_bias_lr', type=float, default=0.1, help='Warmup initial bias lr')
    
    # Loss function weights (critical for performance!)
    parser.add_argument('--box', type=float, default=8.0, help='Box loss gain (optimized for room detection)')
    parser.add_argument('--cls', type=float, default=0.3, help='Class loss gain (lower for single class)')
    parser.add_argument('--dfl', type=float, default=2.0, help='DFL loss gain (better box precision)')
    parser.add_argument('--pose', type=float, default=12.0, help='Pose loss gain (unused for detection)')
    parser.add_argument('--kobj', type=float, default=2.0, help='Keypoint obj loss gain (unused)')
    parser.add_argument('--label_smoothing', type=float, default=0.0, help='Label smoothing epsilon')
    
    # Data augmentation (Conservative - Blueprint-Safe Only)
    parser.add_argument('--hsv_h', type=float, default=0.0, help='Image HSV-Hue augmentation (0.0 = no hue change for blueprints)')
    parser.add_argument('--hsv_s', type=float, default=0.5, help='Image HSV-Saturation augmentation (moderate for color variation)')
    parser.add_argument('--hsv_v', type=float, default=0.3, help='Image HSV-Value augmentation (moderate for brightness)')
    parser.add_argument('--degrees', type=float, default=0.0, help='Image rotation (+/- deg) (0.0 = CRITICAL - preserves orientation)')
    parser.add_argument('--translate', type=float, default=0.05, help='Image translation (+/- fraction) (small, safe)')
    parser.add_argument('--scale', type=float, default=0.3, help='Image scale (+/- gain) (moderate, handles different scales)')
    parser.add_argument('--shear', type=float, default=0.0, help='Image shear (+/- deg) (0.0 = CRITICAL - preserves rectangular shapes)')
    parser.add_argument('--perspective', type=float, default=0.0, help='Image perspective (+/- fraction) (0.0 = CRITICAL - preserves geometry)')
    parser.add_argument('--flipud', type=float, default=0.0, help='Image flip up-down (probability) (0.0 = preserves orientation)')
    parser.add_argument('--fliplr', type=float, default=0.5, help='Image flip left-right (probability) (safe for floor plans)')
    parser.add_argument('--mosaic', type=float, default=0.0, help='Image mosaic (probability) (0.0 = disabled, risky for blueprints)')
    parser.add_argument('--mixup', type=float, default=0.0, help='Image mixup (probability) (0.0 = disabled, risky for blueprints)')
    parser.add_argument('--copy_paste', type=float, default=0.0, help='Segment copy-paste (probability) (not needed for detection)')
    
    # Training configuration
    parser.add_argument('--patience', type=int, default=150, help='Early stopping patience (higher for less augmentation)')
    parser.add_argument('--save_period', type=int, default=-1, help='Save checkpoint every N epochs (-1 = only best)')
    parser.add_argument('--workers', type=int, default=8, help='Data loading workers')
    parser.add_argument('--device', type=str, default='', help='Device (cuda device, i.e. 0 or 0,1,2,3 or cpu)')
    parser.add_argument('--project', type=str, default='', help='Project name (overridden by output-dir)')
    parser.add_argument('--name', type=str, default='yolov8_training', help='Experiment name')
    parser.add_argument('--exist_ok', type=str2bool, default=False, help='Existing project/name ok, do not increment')
    parser.add_argument('--pretrained', type=str2bool, default=True, help='Use pretrained weights (fine-tuning)')
    parser.add_argument('--optimizer', type=str, default='SGD', choices=['SGD', 'Adam', 'AdamW', 'RMSProp'],
                       help='Optimizer (SGD recommended for detection)')
    parser.add_argument('--verbose', type=str2bool, default=True, help='Verbose mode')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--deterministic', type=str2bool, default=False, help='Deterministic mode')
    parser.add_argument('--single_cls', type=str2bool, default=True, help='Train as single-class dataset')
    parser.add_argument('--rect', type=str2bool, default=False, help='Rectangular training')
    parser.add_argument('--cos_lr', type=str2bool, default=True, help='Cosine LR scheduler (smooth decay)')
    parser.add_argument('--close_mosaic', type=int, default=0, help='Disable mosaic augmentation for last N epochs (0 = mosaic disabled)')
    parser.add_argument('--resume', type=str, default='', help='Resume training from checkpoint')
    parser.add_argument('--amp', type=str2bool, default=True, help='Automatic Mixed Precision training')
    parser.add_argument('--fraction', type=float, default=1.0, help='Dataset fraction to use')
    parser.add_argument('--profile', type=str2bool, default=False, help='Profile ONNX and TensorRT speeds')
    parser.add_argument('--freeze', type=int, default=0, help='Freeze layers: backbone=10, first3=0 1 2')
    parser.add_argument('--multi_scale', type=str2bool, default=False, help='Multi-scale training')
    
    # Advanced options
    parser.add_argument('--overlap_mask', type=str2bool, default=False, help='Masks should overlap during training')
    parser.add_argument('--mask_ratio', type=int, default=4, help='Mask downsample ratio')
    parser.add_argument('--dropout', type=float, default=0.0, help='Use dropout regularization')
    parser.add_argument('--val', type=str2bool, default=True, help='Validate/test during training')
    
    return parser.parse_args()


def create_dataset_yaml(train_dir, val_dir, output_path):
    """Create YOLOv8 dataset YAML file."""
    dataset_config = {
        'path': '/opt/ml/input/data',
        'train': 'training/images',
        'val': 'validation/images',
        'nc': 1,
        'names': ['room']
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)
    
    print(f"Created dataset YAML at: {output_path}")
    return output_path


def train_model(args):
    """Train YOLOv8 model with advanced hyperparameters."""
    print("=" * 80)
    print("Advanced YOLOv8 Training Configuration")
    print("=" * 80)
    
    # Set random seed for reproducibility
    if args.seed > 0:
        import random
        import numpy as np
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)
        print(f"✓ Random seed set to: {args.seed}")
    
    # Device configuration
    device = args.device if args.device else ('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    if device.startswith('cuda'):
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    # Verify data directories
    train_images = Path(args.train) / 'images'
    train_labels = Path(args.train) / 'labels'
    val_images = Path(args.val_dir) / 'images'
    val_labels = Path(args.val_dir) / 'labels'
    
    for dir_path, name in [(train_images, 'train images'), 
                           (train_labels, 'train labels'),
                           (val_images, 'val images'),
                           (val_labels, 'val labels')]:
        if not dir_path.exists():
            raise FileNotFoundError(f"{name} directory not found: {dir_path}")
        file_count = len(list(dir_path.glob('*')))
        print(f"✓ {name}: {dir_path} ({file_count} files)")
    
    # Create dataset YAML
    dataset_yaml = Path(args.output_dir) / 'dataset.yaml'
    create_dataset_yaml(args.train, args.val_dir, dataset_yaml)
    
    # Initialize model
    print(f"\nInitializing YOLOv8 model: {args.model_size}")
    model = YOLO(args.model_size)
    
    # Print hyperparameter summary
    print("\n" + "=" * 80)
    print("Hyperparameter Configuration")
    print("=" * 80)
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"Image size: {args.img_size}")
    print(f"Learning rate: {args.lr0} → {args.lr0 * args.lrf} (final)")
    print(f"Optimizer: {args.optimizer}")
    print(f"Momentum: {args.momentum}")
    print(f"Weight decay: {args.weight_decay}")
    print(f"Warmup epochs: {args.warmup_epochs}")
    print(f"Cosine LR scheduler: {args.cos_lr}")
    print(f"\nLoss Function Weights:")
    print(f"  Box loss: {args.box}")
    print(f"  Class loss: {args.cls}")
    print(f"  DFL loss: {args.dfl}")
    print(f"  Label smoothing: {args.label_smoothing}")
    print(f"\nData Augmentation:")
    print(f"  HSV augmentation: H={args.hsv_h}, S={args.hsv_s}, V={args.hsv_v}")
    print(f"  Translation: {args.translate}")
    print(f"  Scale: {args.scale}")
    print(f"  Flip LR: {args.fliplr}")
    print(f"  Mosaic: {args.mosaic}")
    print(f"  Mixup: {args.mixup}")
    print(f"  Close mosaic at epoch: {args.close_mosaic}")
    print(f"\nTraining Options:")
    print(f"  Early stopping patience: {args.patience}")
    print(f"  AMP training: {args.amp}")
    print(f"  Multi-scale: {args.multi_scale}")
    print(f"  Workers: {args.workers}")
    print("=" * 80)
    
    # Prepare training arguments
    train_args = {
        'data': str(dataset_yaml),
        'epochs': args.epochs,
        'batch': args.batch_size,
        'imgsz': args.img_size,
        'lr0': args.lr0,
        'lrf': args.lrf,
        'momentum': args.momentum,
        'weight_decay': args.weight_decay,
        'warmup_epochs': args.warmup_epochs,
        'warmup_momentum': args.warmup_momentum,
        'warmup_bias_lr': args.warmup_bias_lr,
        'box': args.box,
        'cls': args.cls,
        'dfl': args.dfl,
        'pose': args.pose,
        'kobj': args.kobj,
        'label_smoothing': args.label_smoothing,
        'hsv_h': args.hsv_h,
        'hsv_s': args.hsv_s,
        'hsv_v': args.hsv_v,
        'degrees': args.degrees,
        'translate': args.translate,
        'scale': args.scale,
        'shear': args.shear,
        'perspective': args.perspective,
        'flipud': args.flipud,
        'fliplr': args.fliplr,
        'mosaic': args.mosaic,
        'mixup': args.mixup,
        'copy_paste': args.copy_paste,
        'patience': args.patience,
        'save_period': args.save_period,
        'project': args.output_dir if not args.project else args.project,
        'name': args.name,
        'exist_ok': args.exist_ok,
        'pretrained': args.pretrained,
        'optimizer': args.optimizer,
        'verbose': args.verbose,
        'seed': args.seed,
        'deterministic': args.deterministic,
        'single_cls': args.single_cls,
        'rect': args.rect,
        'cos_lr': args.cos_lr,
        'close_mosaic': args.close_mosaic,
        'resume': args.resume if args.resume else False,
        'amp': args.amp,
        'fraction': args.fraction,
        'profile': args.profile,
        'freeze': args.freeze,
        'multi_scale': args.multi_scale,
        'overlap_mask': args.overlap_mask,
        'mask_ratio': args.mask_ratio,
        'dropout': args.dropout,
        'val': args.val,  # Boolean flag for validation during training
        'device': device,
        'workers': args.workers,
    }
    
    # Start training
    print("\n" + "=" * 80)
    print("Starting Training...")
    print("=" * 80)
    
    results = model.train(**train_args)
    
    # Save comprehensive metrics
    metrics_path = Path(args.output_dir) / 'training_metrics.json'
    metrics = {
        'hyperparameters': {
            'epochs': args.epochs,
            'batch_size': args.batch_size,
            'img_size': args.img_size,
            'model_size': args.model_size,
            'lr0': args.lr0,
            'lrf': args.lrf,
            'optimizer': args.optimizer,
            'momentum': args.momentum,
            'weight_decay': args.weight_decay,
            'loss_weights': {
                'box': args.box,
                'cls': args.cls,
                'dfl': args.dfl,
            },
            'augmentation': {
                'hsv_h': args.hsv_h,
                'hsv_s': args.hsv_s,
                'hsv_v': args.hsv_v,
                'translate': args.translate,
                'scale': args.scale,
                'mosaic': args.mosaic,
                'mixup': args.mixup,
            },
        },
        'device': device,
        'final_metrics': {
            'train/box_loss': float(results.results_dict.get('train/box_loss', 0)),
            'train/cls_loss': float(results.results_dict.get('train/cls_loss', 0)),
            'train/dfl_loss': float(results.results_dict.get('train/dfl_loss', 0)),
            'metrics/precision(B)': float(results.results_dict.get('metrics/precision(B)', 0)),
            'metrics/recall(B)': float(results.results_dict.get('metrics/recall(B)', 0)),
            'metrics/mAP50(B)': float(results.results_dict.get('metrics/mAP50(B)', 0)),
            'metrics/mAP50-95(B)': float(results.results_dict.get('metrics/mAP50-95(B)', 0)),
        }
    }
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\n✓ Training metrics saved to: {metrics_path}")
    
    # Save best model
    best_model_path = Path(args.output_dir) / args.name / 'weights' / 'best.pt'
    if best_model_path.exists():
        import shutil
        shutil.copy2(best_model_path, Path(args.model_dir) / 'model.pt')
        print(f"✓ Best model saved to: {args.model_dir}/model.pt")
        
        # Also save metrics alongside model
        shutil.copy2(metrics_path, Path(args.model_dir) / 'training_metrics.json')
    else:
        print("⚠ Warning: Best model not found")
        last_model_path = Path(args.output_dir) / args.name / 'weights' / 'last.pt'
        if last_model_path.exists():
            import shutil
            shutil.copy2(last_model_path, Path(args.model_dir) / 'model.pt')
            print(f"✓ Last model saved to: {args.model_dir}/model.pt")
    
    print("\n" + "=" * 80)
    print("Training Completed Successfully!")
    print("=" * 80)
    print(f"\nFinal Metrics:")
    print(f"  mAP50: {metrics['final_metrics']['metrics/mAP50(B)']:.4f}")
    print(f"  mAP50-95: {metrics['final_metrics']['metrics/mAP50-95(B)']:.4f}")
    print(f"  Precision: {metrics['final_metrics']['metrics/precision(B)']:.4f}")
    print(f"  Recall: {metrics['final_metrics']['metrics/recall(B)']:.4f}")
    
    return results


if __name__ == '__main__':
    args = parse_args()
    
    try:
        train_model(args)
    except Exception as e:
        print(f"\n❌ Training failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
