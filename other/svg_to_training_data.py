#!/usr/bin/env python3
"""
Convert SVG floor plans to PNG images and generate YOLO format labels.
This creates training-ready data from structured SVG files.
"""

import xml.etree.ElementTree as ET
import json
import os
import sys
from pathlib import Path

try:
    from cairosvg import svg2png
    HAS_CAIRO = True
except ImportError:
    HAS_CAIRO = False
    print("Warning: cairosvg not installed. Install with: pip install cairosvg")
    print("SVG to PNG conversion will be skipped.")

def parse_polygon_points(points_str):
    """Parse SVG polygon points string into list of (x, y) tuples."""
    if not points_str:
        return []
    
    coords = [float(x) for x in points_str.replace(',', ' ').split() if x.strip()]
    points = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
    return points

def calculate_bounding_box(points):
    """Calculate bounding box from polygon points."""
    if not points:
        return None
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    return [min(xs), min(ys), max(xs), max(ys)]

def bbox_to_yolo_format(bbox, img_width, img_height):
    """
    Convert bounding box [x_min, y_min, x_max, y_max] to YOLO format.
    YOLO format: class_id center_x center_y width height (all normalized 0-1)
    """
    x_min, y_min, x_max, y_max = bbox
    
    # Calculate center and dimensions
    center_x = (x_min + x_max) / 2.0
    center_y = (y_min + y_max) / 2.0
    width = x_max - x_min
    height = y_max - y_min
    
    # Normalize to 0-1
    center_x_norm = center_x / img_width
    center_y_norm = center_y / img_height
    width_norm = width / img_width
    height_norm = height / img_height
    
    # Clamp to [0, 1]
    center_x_norm = max(0.0, min(1.0, center_x_norm))
    center_y_norm = max(0.0, min(1.0, center_y_norm))
    width_norm = max(0.0, min(1.0, width_norm))
    height_norm = max(0.0, min(1.0, height_norm))
    
    return center_x_norm, center_y_norm, width_norm, height_norm

def extract_rooms_from_svg(svg_path):
    """Extract all rooms from an SVG file."""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {svg_path}: {e}", file=sys.stderr)
        return None
    
    # Get SVG dimensions
    svg_width = float(root.get('width', 1000))
    svg_height = float(root.get('height', 1000))
    
    viewbox = root.get('viewBox', '')
    if viewbox:
        parts = viewbox.split()
        if len(parts) >= 4:
            svg_width = float(parts[2])
            svg_height = float(parts[3])
    
    rooms = []
    
    # Find all Space elements
    for elem in root.iter():
        class_attr = elem.get('class', '')
        if 'Space' in class_attr and not class_attr.startswith('SpaceDimensions'):
            # Find polygon within this space element
            polygon = None
            for child in elem.iter():
                if child.tag.endswith('polygon'):
                    polygon = child
                    break
            
            if polygon is not None:
                points_str = polygon.get('points', '')
                points = parse_polygon_points(points_str)
                
                if points:
                    bbox = calculate_bounding_box(points)
                    if bbox:
                        rooms.append({
                            'bbox': bbox,
                            'class': class_attr
                        })
    
    return {
        'width': svg_width,
        'height': svg_height,
        'rooms': rooms
    }

def convert_svg_to_png(svg_path, png_path, width=1024, height=1024):
    """Convert SVG to PNG using cairosvg."""
    if not HAS_CAIRO:
        print(f"Skipping PNG conversion for {svg_path} (cairosvg not installed)")
        return False
    
    try:
        svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=width,
            output_height=height
        )
        return True
    except Exception as e:
        print(f"Error converting {svg_path} to PNG: {e}", file=sys.stderr)
        return False

def process_svg_for_training(svg_path, output_dir, class_mapping=None, target_size=1024):
    """
    Process a single SVG file:
    1. Extract room bounding boxes
    2. Convert SVG to PNG
    3. Generate YOLO format label file
    """
    svg_path = Path(svg_path)
    output_dir = Path(output_dir)
    
    # Default class mapping (all rooms = class 0)
    if class_mapping is None:
        class_mapping = {'room': 0}
    
    # Extract rooms
    result = extract_rooms_from_svg(svg_path)
    if not result or not result['rooms']:
        print(f"No rooms found in {svg_path.name}")
        return False
    
    # Convert SVG to PNG
    png_path = output_dir / f"{svg_path.stem}.png"
    svg_width = result['width']
    svg_height = result['height']
    
    # Maintain aspect ratio
    aspect_ratio = svg_width / svg_height
    if aspect_ratio > 1:
        png_width = target_size
        png_height = int(target_size / aspect_ratio)
    else:
        png_height = target_size
        png_width = int(target_size * aspect_ratio)
    
    if not convert_svg_to_png(svg_path, png_path, png_width, png_height):
        return False
    
    # Generate YOLO label file
    label_path = output_dir / f"{svg_path.stem}.txt"
    
    with open(label_path, 'w') as f:
        for room in result['rooms']:
            bbox = room['bbox']
            
            # Scale bbox to PNG dimensions (if SVG was resized)
            scale_x = png_width / svg_width
            scale_y = png_height / svg_height
            
            scaled_bbox = [
                bbox[0] * scale_x,
                bbox[1] * scale_y,
                bbox[2] * scale_x,
                bbox[3] * scale_y
            ]
            
            # Convert to YOLO format
            center_x, center_y, width, height = bbox_to_yolo_format(
                scaled_bbox, png_width, png_height
            )
            
            # Use class 0 for all rooms (you can customize this)
            class_id = 0
            
            # Write YOLO format: class_id center_x center_y width height
            f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
    
    print(f"✓ Processed {svg_path.name}: {len(result['rooms'])} rooms")
    return True

def process_directory(svg_dir, output_dir, target_size=1024):
    """Process all SVG files in a directory."""
    svg_dir = Path(svg_dir)
    output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    svg_files = list(svg_dir.glob("*.svg"))
    
    if not svg_files:
        print(f"No SVG files found in {svg_dir}")
        return
    
    print(f"Processing {len(svg_files)} SVG files...")
    
    success_count = 0
    for svg_file in svg_files:
        if process_svg_for_training(svg_file, output_dir, target_size=target_size):
            success_count += 1
    
    print(f"\n✓ Successfully processed {success_count}/{len(svg_files)} files")
    print(f"✓ Output directory: {output_dir}")
    print(f"\nNext steps:")
    print(f"1. Review the generated PNG images and .txt label files")
    print(f"2. Split into train/val/test sets (e.g., 70/15/15)")
    print(f"3. Organize for YOLO training:")
    print(f"   - images/train/")
    print(f"   - labels/train/")
    print(f"   - images/val/")
    print(f"   - labels/val/")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python svg_to_training_data.py <svg_file_or_directory> <output_directory> [target_size]")
        print("\nExample:")
        print("  python svg_to_training_data.py blueprint.svg output/")
        print("  python svg_to_training_data.py svg_dataset/ training_data/ 1024")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    target_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    
    if input_path.is_file():
        process_svg_for_training(input_path, output_dir, target_size=target_size)
    elif input_path.is_dir():
        process_directory(input_path, output_dir, target_size=target_size)
    else:
        print(f"Path not found: {input_path}", file=sys.stderr)
        sys.exit(1)

