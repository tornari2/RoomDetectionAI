#!/usr/bin/env python3
"""
Improved bounding box extraction that accounts for SVG viewBox offsets.
This ensures bounding boxes align with the actual wall boundaries in PNG images.
"""

import xml.etree.ElementTree as ET
import json
import sys
from pathlib import Path

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

def get_svg_dimensions_and_offset(root):
    """Extract SVG dimensions and viewBox offset."""
    # Get width/height
    svg_width = float(root.get('width', 1000))
    svg_height = float(root.get('height', 1000))
    
    # Check viewBox for offset
    viewbox = root.get('viewBox', '')
    offset_x = 0
    offset_y = 0
    
    if viewbox:
        parts = viewbox.split()
        if len(parts) >= 4:
            # viewBox format: "x y width height"
            offset_x = float(parts[0]) if parts[0] else 0
            offset_y = float(parts[1]) if parts[1] else 0
            svg_width = float(parts[2])
            svg_height = float(parts[3])
    
    return svg_width, svg_height, offset_x, offset_y

def extract_rooms_from_svg_improved(svg_path):
    """Extract rooms accounting for viewBox offsets."""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {svg_path}: {e}", file=sys.stderr)
        return None
    
    # Get SVG dimensions and offsets
    svg_width, svg_height, offset_x, offset_y = get_svg_dimensions_and_offset(root)
    
    rooms = []
    room_id_counter = 1
    
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
                    # Adjust points for viewBox offset
                    adjusted_points = [(p[0] - offset_x, p[1] - offset_y) for p in points]
                    bbox = calculate_bounding_box(adjusted_points)
                    
                    if bbox:
                        room_data = {
                            "id": f"room_{room_id_counter:03d}",
                            "bounding_box": bbox,
                            "original_bbox": bbox,  # Already adjusted
                            "confidence": 1.0
                        }
                        
                        rooms.append(room_data)
                        room_id_counter += 1
    
    return {
        "svg_file": Path(svg_path).name,
        "svg_width": svg_width,
        "svg_height": svg_height,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "rooms": rooms,
        "total_rooms": len(rooms)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_svg_offset.py <svg_file>")
        sys.exit(1)
    
    result = extract_rooms_from_svg_improved(sys.argv[1])
    if result:
        print(json.dumps(result, indent=2))

