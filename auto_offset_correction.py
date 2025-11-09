#!/usr/bin/env python3
"""
Automatic offset detection and correction for SVG-to-PNG alignment.
Detects systematic offset by analyzing room positions and corrects bounding boxes.
"""

import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import numpy as np
from pathlib import Path
import sys

def parse_points(points_str):
    """Parse SVG polygon points."""
    if not points_str:
        return []
    coords = [float(x) for x in points_str.replace(',', ' ').split() if x.strip()]
    return [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]

def detect_wall_positions(png_array, threshold=50):
    """Detect wall positions in PNG to help with alignment."""
    height, width = png_array.shape
    
    # Find horizontal walls
    h_walls = []
    for y in range(height):
        wall_pixels = np.sum(png_array[y, :] < threshold)
        if wall_pixels > width * 0.1:
            h_walls.append(y)
    
    # Find vertical walls
    v_walls = []
    for x in range(width):
        wall_pixels = np.sum(png_array[:, x] < threshold)
        if wall_pixels > height * 0.1:
            v_walls.append(x)
    
    return h_walls, v_walls

def detect_offset_by_wall_alignment(svg_path, png_path):
    """
    Detect offset by trying to align SVG room edges with detected walls in PNG.
    """
    # Parse SVG
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
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
    png_array = np.array(img.convert('L'))
    img_width, img_height = img.size
    
    scale_x = img_width / svg_width
    scale_y = img_height / svg_height
    
    # Detect walls in PNG
    h_walls, v_walls = detect_wall_positions(png_array)
    
    # Extract SVG room edges
    svg_h_edges = set()
    svg_v_edges = set()
    
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
                    # Get bounding box edges
                    xs = [p[0] for p in svg_points]
                    ys = [p[1] for p in svg_points]
                    
                    # Transform to PNG scale (not yet offset)
                    x_min = min(xs) * scale_x
                    x_max = max(xs) * scale_x
                    y_min = min(ys) * scale_y
                    y_max = max(ys) * scale_y
                    
                    svg_h_edges.add(int(y_min))
                    svg_h_edges.add(int(y_max))
                    svg_v_edges.add(int(x_min))
                    svg_v_edges.add(int(x_max))
    
    # Find best offset by matching edges to walls
    best_offset_x = 0
    best_offset_y = 0
    best_matches_x = 0
    best_matches_y = 0
    
    # Try different X offsets
    for offset_x in range(-50, 51, 5):
        matches = 0
        for edge in svg_v_edges:
            adjusted_edge = edge + offset_x
            # Check if near any wall
            for wall in v_walls:
                if abs(adjusted_edge - wall) < 10:
                    matches += 1
                    break
        if matches > best_matches_x:
            best_matches_x = matches
            best_offset_x = offset_x
    
    # Try different Y offsets
    for offset_y in range(-50, 51, 5):
        matches = 0
        for edge in svg_h_edges:
            adjusted_edge = edge + offset_y
            # Check if near any wall
            for wall in h_walls:
                if abs(adjusted_edge - wall) < 10:
                    matches += 1
                    break
        if matches > best_matches_y:
            best_matches_y = matches
            best_offset_y = offset_y
    
    return best_offset_x, best_offset_y, scale_x, scale_y

def label_with_auto_correction(svg_path, png_path, output_path):
    """Label PNG with automatic offset correction."""
    # Detect offset
    print("Detecting offset...")
    offset_x, offset_y, scale_x, scale_y = detect_offset_by_wall_alignment(svg_path, png_path)
    print(f"Detected offset: x={offset_x}, y={offset_y}")
    
    # Parse SVG
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
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
    draw = ImageDraw.Draw(img)
    
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
                    # Transform with detected offset
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
                    room_count += 1
    
    img.save(output_path)
    print(f"Labeled {room_count} rooms with offset correction")
    return offset_x, offset_y

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python auto_offset_correction.py <svg_path> <png_path> <output_path>")
        sys.exit(1)
    
    svg_path = sys.argv[1]
    png_path = sys.argv[2]
    output_path = sys.argv[3]
    
    label_with_auto_correction(svg_path, png_path, output_path)

