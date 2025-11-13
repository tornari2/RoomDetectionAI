#!/usr/bin/env python3
"""
Evaluate model performance by extracting metrics from training logs and metrics file.
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime


def parse_metrics_from_logs(log_text):
    """Extract metrics from log text."""
    metrics = {}
    
    # Patterns for different metric formats
    patterns = {
        'mAP50': [
            r'mAP50[:\s]+([\d.]+)',
            r'mAP50\(B\)[:\s]+([\d.]+)',
            r'metrics/mAP50\(B\)[:\s]+([\d.]+)',
        ],
        'mAP50-95': [
            r'mAP50-95[:\s]+([\d.]+)',
            r'mAP50-95\(B\)[:\s]+([\d.]+)',
            r'metrics/mAP50-95\(B\)[:\s]+([\d.]+)',
        ],
        'precision': [
            r'precision[:\s]+([\d.]+)',
            r'precision\(B\)[:\s]+([\d.]+)',
            r'metrics/precision\(B\)[:\s]+([\d.]+)',
        ],
        'recall': [
            r'recall[:\s]+([\d.]+)',
            r'recall\(B\)[:\s]+([\d.]+)',
            r'metrics/recall\(B\)[:\s]+([\d.]+)',
        ],
    }
    
    for metric_name, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, log_text, re.IGNORECASE)
            if match:
                try:
                    metrics[metric_name] = float(match.group(1))
                    break
                except ValueError:
                    continue
    
    return metrics


def load_metrics_json(metrics_path):
    """Load metrics from JSON file."""
    try:
        with open(metrics_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Warning: Could not load metrics JSON: {e}")
        return None


def format_metrics_report(metrics_json=None, log_metrics=None):
    """Format a comprehensive metrics report."""
    print("=" * 80)
    print("Model Performance Evaluation")
    print("=" * 80)
    print()
    
    # Get metrics from JSON if available
    if metrics_json:
        print("📊 Training Metrics (from training_metrics.json):")
        print("-" * 80)
        
        if 'final_metrics' in metrics_json:
            final = metrics_json['final_metrics']
            for key, value in sorted(final.items()):
                if isinstance(value, (int, float)):
                    print(f"  {key:40s}: {value:.4f}")
                else:
                    print(f"  {key:40s}: {value}")
        
        if 'training_summary' in metrics_json:
            print("\n📈 Training Summary:")
            print("-" * 80)
            summary = metrics_json['training_summary']
            for key, value in sorted(summary.items()):
                print(f"  {key:40s}: {value}")
        
        print()
    
    # Get metrics from logs if available
    if log_metrics:
        print("📋 Metrics Extracted from Logs:")
        print("-" * 80)
        for key, value in sorted(log_metrics.items()):
            print(f"  {key:40s}: {value:.4f}")
        print()
    
    # Performance interpretation
    print("📊 Performance Interpretation:")
    print("-" * 80)
    
    # Get the best available metrics
    mAP50 = None
    mAP50_95 = None
    precision = None
    recall = None
    
    if metrics_json and 'final_metrics' in metrics_json:
        final = metrics_json['final_metrics']
        mAP50 = final.get('metrics/mAP50(B)') or final.get('mAP50')
        mAP50_95 = final.get('metrics/mAP50-95(B)') or final.get('mAP50-95')
        precision = final.get('metrics/precision(B)') or final.get('precision')
        recall = final.get('metrics/recall(B)') or final.get('recall')
    
    if log_metrics:
        mAP50 = mAP50 or log_metrics.get('mAP50')
        mAP50_95 = mAP50_95 or log_metrics.get('mAP50-95')
        precision = precision or log_metrics.get('precision')
        recall = recall or log_metrics.get('recall')
    
    if mAP50 is not None:
        print(f"  mAP50: {mAP50:.4f}")
        if mAP50 >= 0.9:
            print("    ✅ Excellent - Model performs very well at IoU=0.5")
        elif mAP50 >= 0.7:
            print("    ✅ Good - Model performs well at IoU=0.5")
        elif mAP50 >= 0.5:
            print("    ⚠️  Moderate - Model has room for improvement")
        else:
            print("    ❌ Poor - Model needs significant improvement")
    
    if mAP50_95 is not None:
        print(f"  mAP50-95: {mAP50_95:.4f}")
        if mAP50_95 >= 0.5:
            print("    ✅ Excellent - Model performs well across IoU thresholds")
        elif mAP50_95 >= 0.3:
            print("    ✅ Good - Model performs reasonably across IoU thresholds")
        elif mAP50_95 >= 0.2:
            print("    ⚠️  Moderate - Model needs improvement")
        else:
            print("    ❌ Poor - Model needs significant improvement")
    
    if precision is not None:
        print(f"  Precision: {precision:.4f}")
        if precision >= 0.9:
            print("    ✅ Excellent - Very few false positives")
        elif precision >= 0.7:
            print("    ✅ Good - Low false positive rate")
        elif precision >= 0.5:
            print("    ⚠️  Moderate - Some false positives")
        else:
            print("    ❌ Poor - High false positive rate")
    
    if recall is not None:
        print(f"  Recall: {recall:.4f}")
        if recall >= 0.9:
            print("    ✅ Excellent - Detects most objects")
        elif recall >= 0.7:
            print("    ✅ Good - Detects most objects")
        elif recall >= 0.5:
            print("    ⚠️  Moderate - Misses some objects")
        else:
            print("    ❌ Poor - Misses many objects")
    
    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Evaluate model performance')
    parser.add_argument(
        '--metrics-file',
        type=str,
        help='Path to training_metrics.json file'
    )
    parser.add_argument(
        '--job-name',
        type=str,
        default='yolov8-room-detection-20251108-224902',
        help='Training job name (to find metrics file automatically)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='sagemaker/outputs/model_artifacts',
        help='Directory containing model artifacts'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Path to log file to extract metrics from'
    )
    
    args = parser.parse_args()
    
    # Determine metrics file path
    if args.metrics_file:
        metrics_path = Path(args.metrics_file)
    else:
        metrics_path = Path(args.output_dir) / args.job_name / 'training_metrics.json'
    
    # Load metrics from JSON
    metrics_json = None
    if metrics_path.exists():
        metrics_json = load_metrics_json(metrics_path)
    else:
        print(f"⚠️  Metrics file not found: {metrics_path}")
    
    # Load metrics from logs if provided
    log_metrics = None
    if args.log_file:
        with open(args.log_file, 'r') as f:
            log_text = f.read()
        log_metrics = parse_metrics_from_logs(log_text)
    
    # Generate report
    format_metrics_report(metrics_json, log_metrics)
    
    # Save summary
    if metrics_json or log_metrics:
        summary_path = Path(args.output_dir) / args.job_name / 'performance_summary.txt'
        with open(summary_path, 'w') as f:
            f.write(f"Model Performance Evaluation\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            if metrics_json:
                f.write(json.dumps(metrics_json, indent=2))
            if log_metrics:
                f.write("\n\nLog Metrics:\n")
                f.write(json.dumps(log_metrics, indent=2))
        print(f"\n💾 Summary saved to: {summary_path}")


if __name__ == '__main__':
    main()

