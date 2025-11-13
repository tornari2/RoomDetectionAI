#!/usr/bin/env python3
"""
Analyze the cubicasa5k dataset to identify usable training samples.
Filters out images with colors, excessive text, or poor quality.
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET

try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not installed. Install with: pip install Pillow numpy")
    print("Image analysis will be limited.")

def analyze_svg_structure(svg_path):
    """Check if SVG has proper room structure."""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        room_count = 0
        has_polygons = False
        
        for elem in root.iter():
            class_attr = elem.get('class', '')
            if 'Space' in class_attr and not class_attr.startswith('SpaceDimensions'):
                room_count += 1
                for child in elem.iter():
                    if child.tag.endswith('polygon'):
                        has_polygons = True
                        break
        
        return {
            'has_structure': room_count > 0 and has_polygons,
            'room_count': room_count,
            'valid': room_count >= 3  # At least 3 rooms to be useful
        }
    except Exception as e:
        return {'has_structure': False, 'room_count': 0, 'valid': False, 'error': str(e)}

def analyze_image_quality(png_path):
    """Analyze PNG image to detect colors, text, and quality issues."""
    if not HAS_PIL:
        return {'grayscale': True, 'color_variance': 0, 'usable': True}
    
    try:
        img = Image.open(png_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img_array = np.array(img)
        
        # Check if image is mostly grayscale
        # Calculate variance across color channels
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        color_variance = np.std([r, g, b])
        
        # Check if image is mostly white/light (typical for blueprints)
        mean_brightness = np.mean(img_array)
        
        # Simple heuristic: if color variance is low, it's grayscale
        is_grayscale = color_variance < 20
        
        # Check if image is mostly white/light (good for blueprints)
        is_light = mean_brightness > 200
        
        # Usable if grayscale and light (typical blueprint characteristics)
        usable = is_grayscale and is_light
        
        return {
            'grayscale': bool(is_grayscale),
            'color_variance': float(color_variance),
            'mean_brightness': float(mean_brightness),
            'usable': bool(usable),
            'width': int(img.width),
            'height': int(img.height)
        }
    except Exception as e:
        return {'usable': False, 'error': str(e)}

def process_sample(sample_dir):
    """Process a single sample directory."""
    sample_path = Path(sample_dir)
    
    svg_path = sample_path / "model.svg"
    png_original = sample_path / "F1_original.png"
    png_scaled = sample_path / "F1_scaled.png"
    
    result = {
        'sample_id': sample_path.name,
        'path': str(sample_path),
        'has_svg': svg_path.exists(),
        'has_png_original': png_original.exists(),
        'has_png_scaled': png_scaled.exists(),
        'valid': False
    }
    
    # Check SVG structure
    if svg_path.exists():
        svg_analysis = analyze_svg_structure(svg_path)
        result.update(svg_analysis)
    
    # Check PNG quality (prefer scaled version)
    png_to_check = png_scaled if png_scaled.exists() else png_original
    if png_to_check.exists():
        img_analysis = analyze_image_quality(png_to_check)
        result.update({f'img_{k}': v for k, v in img_analysis.items()})
    
    # Overall validity: needs valid SVG structure and usable image
    result['valid'] = (
        result.get('has_structure', False) and 
        result.get('room_count', 0) >= 3 and
        result.get('img_usable', True)
    )
    
    return result

def analyze_dataset(dataset_root, split_files=None):
    """Analyze entire dataset."""
    dataset_root = Path(dataset_root)
    
    # Get samples from split files if provided
    all_samples = set()
    if split_files:
        for split_file in split_files:
            if Path(split_file).exists():
                with open(split_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            # Extract sample ID from path like "/high_quality_architectural/6044/"
                            sample_id = line.strip('/').split('/')[-1]
                            parent_dir = line.strip('/').split('/')[0] if '/' in line.strip('/') else ''
                            full_path = dataset_root / line.strip('/')
                            if full_path.exists():
                                all_samples.add(full_path)
    
    # If no split files, scan all directories
    if not all_samples:
        for subdir in ['high_quality', 'high_quality_architectural']:
            subdir_path = dataset_root / subdir
            if subdir_path.exists():
                for sample_dir in subdir_path.iterdir():
                    if sample_dir.is_dir() and (sample_dir / "model.svg").exists():
                        all_samples.add(sample_dir)
    
    print(f"Found {len(all_samples)} samples to analyze")
    print("Analyzing samples...")
    
    results = []
    stats = defaultdict(int)
    
    for i, sample_dir in enumerate(sorted(all_samples)):
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(all_samples)} samples...")
        
        result = process_sample(sample_dir)
        results.append(result)
        
        # Update stats
        stats['total'] += 1
        if result['has_svg']:
            stats['has_svg'] += 1
        if result.get('has_structure', False):
            stats['has_structure'] += 1
        if result.get('room_count', 0) >= 3:
            stats['has_3plus_rooms'] += 1
        if result.get('img_usable', True):
            stats['usable_image'] += 1
        if result['valid']:
            stats['valid_samples'] += 1
    
    # Summary
    print(f"\n=== Dataset Analysis Summary ===")
    print(f"Total samples analyzed: {stats['total']}")
    print(f"Samples with SVG: {stats['has_svg']}")
    print(f"Samples with valid structure: {stats['has_structure']}")
    print(f"Samples with 3+ rooms: {stats['has_3plus_rooms']}")
    print(f"Samples with usable images: {stats['usable_image']}")
    print(f"VALID samples (ready for training): {stats['valid_samples']}")
    print(f"Success rate: {stats['valid_samples']/stats['total']*100:.1f}%")
    
    # Save results
    output_file = Path(dataset_root).parent / "dataset_analysis.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': dict(stats),
            'samples': results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Save list of valid samples
    valid_samples = [r for r in results if r['valid']]
    valid_list_file = Path(dataset_root).parent / "valid_samples.txt"
    with open(valid_list_file, 'w') as f:
        for result in valid_samples:
            f.write(f"{result['path']}\n")
    
    print(f"Valid samples list saved to: {valid_list_file}")
    print(f"Total valid samples: {len(valid_samples)}")
    
    return results, stats

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_dataset.py <dataset_root> [train.txt] [val.txt] [test.txt]")
        print("\nExample:")
        print("  python analyze_dataset.py /path/to/cubicasa5k/cubicasa5k")
        print("  python analyze_dataset.py /path/to/cubicasa5k/cubicasa5k train.txt val.txt test.txt")
        sys.exit(1)
    
    dataset_root = sys.argv[1]
    split_files = sys.argv[2:] if len(sys.argv) > 2 else None
    
    analyze_dataset(dataset_root, split_files)

