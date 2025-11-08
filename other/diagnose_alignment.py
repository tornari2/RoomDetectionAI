#!/usr/bin/env python3
"""
Diagnostic tool to compare SVG room coordinates with PNG images.
Helps identify alignment issues.
"""

import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from pathlib import Path
import sys

def parse_points(points_str):
    """Parse SVG polygon points."""
    if not points_str:
        return []
    coords = [float(x) for x in points_str.replace(',', ' ').split() if x.strip()]
    return [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]

def diagnose_alignment(svg_path, png_path, output_path):
    """Create diagnostic visualization showing SVG vs PNG alignment."""
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
    
    # Create overlay image
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_img = ImageDraw.Draw(img)
    
    scale_x = img_width / svg_width
    scale_y = img_height / svg_height
    
    print(f"SVG: {svg_width:.1f} x {svg_height:.1f}")
    print(f"PNG: {img_width} x {img_height}")
    print(f"Scale: {scale_x:.3f} x {scale_y:.3f}")
    print()
    
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
                    # Transform to PNG
                    png_points = [(int(p[0] * scale_x), int(p[1] * scale_y)) for p in svg_points]
                    
                    # Calculate bbox
                    xs = [p[0] for p in png_points]
                    ys = [p[1] for p in png_points]
                    bbox = [min(xs), min(ys), max(xs), max(ys)]
                    
                    # Draw polygon outline (semi-transparent)
                    draw_overlay.polygon(png_points, outline=(255, 0, 0, 200), width=3)
                    # Draw bounding box
                    draw_img.rectangle(bbox, outline=(255, 0, 0), width=2)
                    
                    # Print first room details
                    if room_count == 0:
                        print(f"First room (room {room_count + 1}):")
                        print(f"  SVG points: {svg_points[:3]}... ({len(svg_points)} points)")
                        print(f"  PNG bbox: {bbox}")
                        print(f"  PNG points: {png_points[:3]}...")
                    
                    room_count += 1
    
    # Composite overlay onto image
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    img.save(output_path)
    
    print(f"\nTotal rooms: {room_count}")
    print(f"Diagnostic image saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python diagnose_alignment.py <svg_path> <png_path> <output_path>")
        sys.exit(1)
    
    diagnose_alignment(sys.argv[1], sys.argv[2], sys.argv[3])

