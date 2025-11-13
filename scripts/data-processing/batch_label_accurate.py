#!/usr/bin/env python3
"""
Improved batch labeling using actual SVG polygon points transformed to PNG coordinates.
This ensures accurate alignment between SVG room definitions and PNG images.
"""

import json
import sys
from pathlib import Path
import subprocess

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not installed. Install with: pip install Pillow")
    sys.exit(1)

def extract_rooms_from_svg(svg_path):
    """Extract rooms using the extract_rooms_from_svg.py script."""
    # Look for extract_rooms_from_svg.py in other/ directory
    extract_script = Path(__file__).parent.parent.parent / 'other' / 'extract_rooms_from_svg.py'
    if not extract_script.exists():
        # Fallback to same directory
        extract_script = Path(__file__).parent / 'extract_rooms_from_svg.py'
    
    result = subprocess.run(
        ['python3', str(extract_script), str(svg_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error extracting from {svg_path}: {result.stderr}", file=sys.stderr)
        return None
    
    try:
        return json.loads(result.stdout)
    except:
        return None

def draw_accurate_bounding_boxes(image_path, rooms_data, output_path, svg_width, svg_height):
    """
    Draw bounding boxes using actual SVG polygon points transformed to PNG coordinates.
    This ensures perfect alignment.
    """
    try:
        import xml.etree.ElementTree as ET
        
        # Load image
        img = Image.open(image_path)
        img_width, img_height = img.size
        draw = ImageDraw.Draw(img)
        
        # Calculate scale factors
        scale_x = img_width / svg_width
        scale_y = img_height / svg_height
        
        # Parse SVG to get actual polygon points
        svg_path = Path(image_path).parent / "model.svg"
        if not svg_path.exists():
            print(f"    Warning: SVG not found, using bbox approximation")
            # Fallback to bbox method
            for room in rooms_data.get('rooms', []):
                original_bbox = room.get('original_bbox', room.get('bounding_box'))
                if not original_bbox:
                    continue
                x_min, y_min, x_max, y_max = original_bbox
                x1 = int(x_min * scale_x)
                y1 = int(y_min * scale_y)
                x2 = int(x_max * scale_x)
                y2 = int(y_max * scale_y)
                draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        else:
            # Use accurate polygon method
            tree = ET.parse(svg_path)
            root = tree.getroot()
            
            def parse_points(points_str):
                if not points_str:
                    return []
                coords = [float(x) for x in points_str.replace(',', ' ').split() if x.strip()]
                return [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
            
            room_idx = 0
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
                    
                    if polygon and room_idx < len(rooms_data.get('rooms', [])):
                        points_str = polygon.get('points', '')
                        svg_points = parse_points(points_str)
                        
                        if svg_points:
                            # Transform to PNG coordinates
                            png_points = [(int(p[0] * scale_x), int(p[1] * scale_y)) for p in svg_points]
                            
                            # Calculate accurate bounding box from transformed polygon points
                            xs = [p[0] for p in png_points]
                            ys = [p[1] for p in png_points]
                            bbox = [min(xs), min(ys), max(xs), max(ys)]
                            
                            # Draw bounding box (calculated from accurate polygon points)
                            draw.rectangle(bbox, outline="red", width=2)
                            
                            room_idx += 1
        
        # Save annotated image
        img.save(output_path)
        return True
    except Exception as e:
        print(f"Error visualizing {image_path}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def process_sample(sample_dir, output_dir):
    """Process a single sample directory."""
    sample_path = Path(sample_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    svg_path = sample_path / "model.svg"
    png_scaled = sample_path / "F1_scaled.png"
    
    if not svg_path.exists():
        print(f"✗ No SVG found: {sample_path}")
        return False
    
    if not png_scaled.exists():
        print(f"✗ No F1_scaled.png found: {sample_path}")
        return False
    
    # Extract rooms from SVG
    print(f"Processing {sample_path.name}...")
    rooms_data = extract_rooms_from_svg(svg_path)
    
    if not rooms_data or not rooms_data.get('rooms'):
        print(f"  ✗ No rooms extracted")
        return False
    
    # Create visualization with accurate coordinates
    output_path = output_dir / f"{sample_path.name}_annotated.png"
    success = draw_accurate_bounding_boxes(
        png_scaled, 
        rooms_data, 
        output_path,
        rooms_data.get('svg_width', 1000),
        rooms_data.get('svg_height', 1000)
    )
    
    if success:
        print(f"  ✓ Created: {output_path.name} ({rooms_data.get('total_rooms', 0)} rooms)")
        return True
    
    return False

def main():
    dataset_root = Path("/Users/michaeltornaritis/Downloads/archive/cubicasa5k/cubicasa5k/high_quality")
    output_dir = Path("/Users/michaeltornaritis/Desktop/WK4_RoomDetectionAI/test_output/batch_annotated")
    
    # Get sample directories
    sample_dirs = sorted([d for d in dataset_root.iterdir() if d.is_dir()])[:15]
    
    print(f"Processing {len(sample_dirs)} samples with accurate polygon-based labeling...\n")
    
    success_count = 0
    for sample_dir in sample_dirs:
        if process_sample(sample_dir, output_dir):
            success_count += 1
            if success_count >= 10:
                break
    
    print(f"\n{'='*60}")
    print(f"✓ Successfully annotated {success_count} blueprints")
    print(f"✓ Output directory: {output_dir}")
    print(f"\nUsing actual SVG polygon points for accurate alignment!")

if __name__ == "__main__":
    main()

