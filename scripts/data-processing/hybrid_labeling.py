#!/usr/bin/env python3
"""
Hybrid approach: Use SVG data but with manual offset correction capability.
Allows you to specify offset/scale adjustments if SVG and PNG don't align perfectly.
"""

import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from pathlib import Path
import json
import sys

def parse_points(points_str):
    """Parse SVG polygon points."""
    if not points_str:
        return []
    coords = [float(x) for x in points_str.replace(',', ' ').split() if x.strip()]
    return [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]

def extract_and_label_with_correction(svg_path, png_path, output_path, 
                                      offset_x=0, offset_y=0, scale_x=None, scale_y=None):
    """
    Extract rooms from SVG and label PNG with optional manual corrections.
    
    Args:
        offset_x, offset_y: Manual offset adjustments
        scale_x, scale_y: Manual scale adjustments (if None, auto-calculate)
    """
    # Parse SVG
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # Get SVG dimensions
    svg_width = float(root.get('width', 1000))
    svg_height = float(root.get('height', 1000))
    viewbox = root.get('viewBox', '')
    if viewbox:
        parts = viewbox.split()
        if len(parts) >= 4:
            svg_width = float(parts[2])
            svg_height = float(parts[3])
    
    # Load PNG
    img = Image.open(png_path)
    img_width, img_height = img.size
    
    # Calculate scale (or use provided)
    if scale_x is None:
        scale_x = img_width / svg_width
    if scale_y is None:
        scale_y = img_height / svg_height
    
    draw = ImageDraw.Draw(img)
    
    rooms = []
    room_count = 0
    
    for elem in root.iter():
        class_attr = elem.get('class', '')
        if 'Space' in class_attr and not class_attr.startswith('SpaceDimensions'):
            if any(excluded in class_attr for excluded in ['Window', 'Door', 'Wall', 'FixedFurniture']):
                continue
            
            polygon = None
            for child in elem.iter():
                if child.tag.endswith('polygon'):
                    polygon = child
                    break
            
            if polygon is not None:
                points_str = polygon.get('points', '')
                svg_points = parse_points(points_str)
                
                if svg_points:
                    # Transform with corrections
                    png_points = [
                        (int((p[0] * scale_x) + offset_x), 
                         int((p[1] * scale_y) + offset_y)) 
                        for p in svg_points
                    ]
                    
                    # Calculate bbox
                    xs = [p[0] for p in png_points]
                    ys = [p[1] for p in png_points]
                    bbox = [min(xs), min(ys), max(xs), max(ys)]
                    
                    # Draw bounding box
                    draw.rectangle(bbox, outline="red", width=3)
                    
                    rooms.append({
                        'id': f"room_{room_count + 1:03d}",
                        'bbox': bbox
                    })
                    room_count += 1
    
    img.save(output_path)
    
    return {
        'rooms': rooms,
        'total_rooms': room_count,
        'scale_x': scale_x,
        'scale_y': scale_y,
        'offset_x': offset_x,
        'offset_y': offset_y
    }

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python hybrid_labeling.py <svg_path> <png_path> <output_path> [offset_x] [offset_y] [scale_x] [scale_y]")
        print("\nExample:")
        print("  python hybrid_labeling.py model.svg F1_scaled.png output.png")
        print("  python hybrid_labeling.py model.svg F1_scaled.png output.png 10 -5")
        print("  python hybrid_labeling.py model.svg F1_scaled.png output.png 0 0 1.0 1.0")
        sys.exit(1)
    
    svg_path = sys.argv[1]
    png_path = sys.argv[2]
    output_path = sys.argv[3]
    
    offset_x = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    offset_y = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    scale_x = float(sys.argv[6]) if len(sys.argv) > 6 else None
    scale_y = float(sys.argv[7]) if len(sys.argv) > 7 else None
    
    result = extract_and_label_with_correction(svg_path, png_path, output_path, 
                                              offset_x, offset_y, scale_x, scale_y)
    print(json.dumps(result, indent=2))

