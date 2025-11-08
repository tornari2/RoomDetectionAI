#!/usr/bin/env python3
"""
Improved bounding box extraction that uses actual SVG polygon points
and properly transforms them to PNG coordinates for accurate alignment.
"""

import xml.etree.ElementTree as ET
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

def parse_polygon_points(points_str):
    """Parse SVG polygon points string into list of (x, y) tuples."""
    if not points_str:
        return []
    
    coords = [float(x) for x in points_str.replace(',', ' ').split() if x.strip()]
    points = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
    return points

def get_svg_dimensions(root):
    """Get SVG dimensions from width/height or viewBox."""
    svg_width = float(root.get('width', 1000))
    svg_height = float(root.get('height', 1000))
    
    viewbox = root.get('viewBox', '')
    if viewbox:
        parts = viewbox.split()
        if len(parts) >= 4:
            svg_width = float(parts[2])
            svg_height = float(parts[3])
    
    return svg_width, svg_height

def transform_points_to_png(points, svg_width, svg_height, png_width, png_height):
    """Transform SVG points to PNG coordinates."""
    scale_x = png_width / svg_width
    scale_y = png_height / svg_height
    
    transformed = [(int(p[0] * scale_x), int(p[1] * scale_y)) for p in points]
    return transformed

def calculate_bbox_from_points(points):
    """Calculate bounding box from polygon points."""
    if not points:
        return None
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    return [min(xs), min(ys), max(xs), max(ys)]

def extract_and_visualize_rooms(svg_path, png_path, output_path):
    """
    Extract rooms from SVG and visualize them directly on PNG with accurate coordinates.
    """
    # Parse SVG
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    svg_width, svg_height = get_svg_dimensions(root)
    
    # Load PNG to get dimensions
    png_img = Image.open(png_path)
    png_width, png_height = png_img.size
    
    # Create drawing context
    draw = ImageDraw.Draw(png_img)
    
    rooms = []
    room_id = 1
    
    # Extract room polygons
    for elem in root.iter():
        class_attr = elem.get('class', '')
        
        # Only process Space elements, exclude windows, doors, walls
        if 'Space' in class_attr and not class_attr.startswith('SpaceDimensions'):
            if any(excluded in class_attr for excluded in ['Window', 'Door', 'Wall', 'FixedFurniture']):
                continue
            
            # Find polygon
            polygon = None
            for child in elem.iter():
                if child.tag.endswith('polygon'):
                    polygon = child
                    break
            
            if polygon:
                points_str = polygon.get('points', '')
                svg_points = parse_polygon_points(points_str)
                
                if svg_points:
                    # Transform points to PNG coordinates
                    png_points = transform_points_to_png(svg_points, svg_width, svg_height, png_width, png_height)
                    
                    # Calculate bounding box from transformed points
                    bbox = calculate_bbox_from_points(png_points)
                    
                    if bbox:
                        # Draw the actual polygon outline (more accurate than rectangle)
                        draw.polygon(png_points, outline="red", width=2)
                        
                        # Also draw bounding box for comparison
                        # draw.rectangle(bbox, outline="blue", width=1)
                        
                        rooms.append({
                            "id": f"room_{room_id:03d}",
                            "bbox": bbox,
                            "polygon_points": png_points
                        })
                        room_id += 1
    
    # Save annotated image
    png_img.save(output_path)
    
    return {
        "svg_file": Path(svg_path).name,
        "png_file": Path(png_path).name,
        "svg_dimensions": [svg_width, svg_height],
        "png_dimensions": [png_width, png_height],
        "rooms": rooms,
        "total_rooms": len(rooms)
    }

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python accurate_labeling.py <svg_path> <png_path> <output_path>")
        sys.exit(1)
    
    svg_path = sys.argv[1]
    png_path = sys.argv[2]
    output_path = sys.argv[3]
    
    result = extract_and_visualize_rooms(svg_path, png_path, output_path)
    print(json.dumps(result, indent=2))

