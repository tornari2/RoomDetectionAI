#!/usr/bin/env python3
"""
Extract room bounding boxes from structured SVG floor plans.
Converts SVG polygon coordinates to normalized 0-1000 bounding boxes.
"""

import xml.etree.ElementTree as ET
import json
import os
import sys
from pathlib import Path

def parse_polygon_points(points_str):
    """Parse SVG polygon points string into list of (x, y) tuples."""
    if not points_str:
        return []
    
    # Split by spaces and commas, filter empty strings
    coords = [float(x) for x in points_str.replace(',', ' ').split() if x.strip()]
    
    # Group into (x, y) pairs
    points = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
    return points

def calculate_bounding_box(points):
    """Calculate bounding box from polygon points."""
    if not points:
        return None
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    x_min = min(xs)
    y_min = min(ys)
    x_max = max(xs)
    y_max = max(ys)
    
    return [x_min, y_min, x_max, y_max]

def normalize_coordinates(bbox, svg_width, svg_height, target_range=1000):
    """Normalize bounding box coordinates to 0-1000 range."""
    if not bbox:
        return None
    
    x_min, y_min, x_max, y_max = bbox
    
    # Normalize to 0-1000
    norm_x_min = int((x_min / svg_width) * target_range)
    norm_y_min = int((y_min / svg_height) * target_range)
    norm_x_max = int((x_max / svg_width) * target_range)
    norm_y_max = int((y_max / svg_height) * target_range)
    
    # Clamp to 0-1000
    norm_x_min = max(0, min(target_range, norm_x_min))
    norm_y_min = max(0, min(target_range, norm_y_min))
    norm_x_max = max(0, min(target_range, norm_x_max))
    norm_y_max = max(0, min(target_range, norm_y_max))
    
    return [norm_x_min, norm_y_min, norm_x_max, norm_y_max]

def extract_room_label(space_element):
    """Extract room label text from space element."""
    # Look for text in NameLabel - traverse the tree
    def find_text_in_namelabel(elem, parent=None):
        for child in elem:
            # Check if this is a NameLabel group
            if child.get('id', '').endswith('NameLabel') or 'NameLabel' in child.get('class', ''):
                # Find text within this NameLabel
                for text_elem in child.iter():
                    if text_elem.tag.endswith('text') and text_elem.text:
                        return text_elem.text.strip()
            # Recursively search
            result = find_text_in_namelabel(child, elem)
            if result:
                return result
        return None
    
    label = find_text_in_namelabel(space_element)
    if label:
        return label
    
    # Fallback: get first text element
    for text_elem in space_element.iter():
        if text_elem.tag.endswith('text') and text_elem.text:
            return text_elem.text.strip()
    
    return None

def extract_room_type(class_attr):
    """Extract room type from class attribute."""
    if not class_attr:
        return "Unknown"
    
    classes = class_attr.split()
    # Find Space class and get type
    for cls in classes:
        if cls != "Space" and "Space" in classes:
            return cls
    return "Unknown"

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
    
    # Try viewBox if width/height not available
    viewbox = root.get('viewBox', '')
    if viewbox:
        parts = viewbox.split()
        if len(parts) >= 4:
            svg_width = float(parts[2])
            svg_height = float(parts[3])
    
    rooms = []
    room_id_counter = 1
    
    # Find all Space elements
    # Handle namespace
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    
    # Search for elements with class containing "Space"
    for elem in root.iter():
        class_attr = elem.get('class', '')
        # Only process Space elements, exclude windows, doors, and other non-room elements
        if 'Space' in class_attr and not class_attr.startswith('SpaceDimensions'):
            # Exclude windows, doors, walls, and other non-room elements
            if any(excluded in class_attr for excluded in ['Window', 'Door', 'Wall', 'FixedFurniture']):
                continue
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
                        # Normalize coordinates
                        norm_bbox = normalize_coordinates(bbox, svg_width, svg_height)
                        
                        # Extract room label
                        room_label = extract_room_label(elem)
                        
                        # Extract room type
                        room_type = extract_room_type(class_attr)
                        
                        room_data = {
                            "id": f"room_{room_id_counter:03d}",
                            "bounding_box": norm_bbox,
                            "confidence": 1.0,  # Since it's from structured data
                            "name_hint": room_label if room_label else None,
                            "room_type": room_type,
                            "original_bbox": bbox  # Keep original for reference
                        }
                        
                        rooms.append(room_data)
                        room_id_counter += 1
    
    return {
        "svg_file": os.path.basename(svg_path),
        "svg_width": svg_width,
        "svg_height": svg_height,
        "rooms": rooms,
        "total_rooms": len(rooms)
    }

def process_svg_directory(svg_dir, output_dir=None):
    """Process all SVG files in a directory."""
    svg_dir = Path(svg_dir)
    
    if not svg_dir.exists():
        print(f"Directory not found: {svg_dir}", file=sys.stderr)
        return
    
    svg_files = list(svg_dir.glob("*.svg"))
    
    if not svg_files:
        print(f"No SVG files found in {svg_dir}", file=sys.stderr)
        return
    
    print(f"Found {len(svg_files)} SVG files")
    
    all_results = []
    
    for svg_file in svg_files:
        print(f"Processing {svg_file.name}...")
        result = extract_rooms_from_svg(svg_file)
        
        if result and result['rooms']:
            all_results.append(result)
            print(f"  ✓ Extracted {result['total_rooms']} rooms")
            
            # Save individual result
            if output_dir:
                output_path = Path(output_dir) / f"{svg_file.stem}_rooms.json"
                with open(output_path, 'w') as f:
                    json.dump(result, f, indent=2)
        else:
            print(f"  ✗ No rooms found")
    
    # Save summary
    if output_dir and all_results:
        summary = {
            "total_files": len(all_results),
            "total_rooms": sum(r['total_rooms'] for r in all_results),
            "files": all_results
        }
        
        summary_path = Path(output_dir) / "extraction_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✓ Processed {len(all_results)} files with {summary['total_rooms']} total rooms")
        print(f"✓ Results saved to {output_dir}")
    
    return all_results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_rooms_from_svg.py <svg_file_or_directory> [output_directory]")
        print("\nExample:")
        print("  python extract_rooms_from_svg.py blueprint.svg")
        print("  python extract_rooms_from_svg.py svg_dataset/ output/")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    input_path = Path(input_path)
    
    if input_path.is_file():
        # Single file
        result = extract_rooms_from_svg(input_path)
        if result:
            print(json.dumps(result, indent=2))
            
            if output_dir:
                output_path = Path(output_dir) / f"{input_path.stem}_rooms.json"
                with open(output_path, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"\n✓ Saved to {output_path}")
    elif input_path.is_dir():
        # Directory
        process_svg_directory(input_path, output_dir)
    else:
        print(f"Path not found: {input_path}", file=sys.stderr)
        sys.exit(1)

