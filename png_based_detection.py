#!/usr/bin/env python3
"""
Alternative approach: Use PNG-based room detection with SVG as reference.
Since SVG-to-PNG alignment isn't perfect, we'll detect rooms directly from PNG images
using wall detection and flood fill, then use SVG as validation/reference.
"""

import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import sys

def detect_rooms_from_png(png_path, min_room_size=5000):
    """
    Detect rooms directly from PNG by:
    1. Detecting walls (dark lines)
    2. Using flood fill to find enclosed spaces
    3. Filtering by size to get actual rooms
    """
    # Load image
    img = Image.open(png_path)
    img_array = np.array(img.convert('L'))  # Grayscale
    height, width = img_array.shape
    
    # Threshold to get walls (dark pixels)
    wall_threshold = 50
    wall_mask = img_array < wall_threshold
    
    # Create binary image: 1 = space, 0 = wall
    space_mask = ~wall_mask
    
    # Use flood fill to find connected components (rooms)
    from scipy import ndimage
    
    try:
        # Label connected components
        labeled, num_features = ndimage.label(space_mask)
        
        rooms = []
        for i in range(1, num_features + 1):
            component = (labeled == i)
            area = np.sum(component)
            
            if area > min_room_size:  # Filter small components
                # Get bounding box
                rows = np.any(component, axis=1)
                cols = np.any(component, axis=0)
                
                if np.any(rows) and np.any(cols):
                    y_min, y_max = np.where(rows)[0][[0, -1]]
                    x_min, x_max = np.where(cols)[0][[0, -1]]
                    
                    rooms.append({
                        'bbox': [int(x_min), int(y_min), int(x_max), int(y_max)],
                        'area': int(area)
                    })
        
        return rooms
    except ImportError:
        print("scipy not available, using simpler method")
        return []

def simple_wall_based_detection(png_path):
    """
    Simpler approach: Detect walls, then find rectangular regions between walls.
    """
    img = Image.open(png_path)
    img_array = np.array(img.convert('L'))
    height, width = img_array.shape
    
    # Detect horizontal and vertical walls
    wall_threshold = 50
    wall_mask = img_array < wall_threshold
    
    # Find horizontal wall lines
    h_walls = []
    for y in range(height):
        wall_pixels = np.sum(wall_mask[y, :])
        if wall_pixels > width * 0.1:  # At least 10% wall
            h_walls.append(y)
    
    # Find vertical wall lines  
    v_walls = []
    for x in range(width):
        wall_pixels = np.sum(wall_mask[:, x])
        if wall_pixels > height * 0.1:  # At least 10% wall
            v_walls.append(x)
    
    # Group nearby walls
    def group_walls(walls, threshold=5):
        if not walls:
            return []
        grouped = []
        current = [walls[0]]
        for w in walls[1:]:
            if w - current[-1] <= threshold:
                current.append(w)
            else:
                grouped.append(int(np.mean(current)))
                current = [w]
        if current:
            grouped.append(int(np.mean(current)))
        return sorted(grouped)
    
    h_walls = group_walls(h_walls)
    v_walls = group_walls(v_walls)
    
    # Find rooms as rectangles between walls
    rooms = []
    for i in range(len(h_walls) - 1):
        for j in range(len(v_walls) - 1):
            y_min = h_walls[i]
            y_max = h_walls[i + 1]
            x_min = v_walls[j]
            x_max = v_walls[j + 1]
            
            # Check if this region has enough space (not just a wall)
            region = img_array[y_min:y_max, x_min:x_max]
            space_pixels = np.sum(region > wall_threshold)
            area = (x_max - x_min) * (y_max - y_min)
            
            if space_pixels > area * 0.5 and area > 1000:  # At least 50% space, min size
                rooms.append({
                    'bbox': [x_min, y_min, x_max, y_max],
                    'area': area
                })
    
    return rooms

def visualize_rooms(png_path, rooms, output_path):
    """Visualize detected rooms on PNG."""
    img = Image.open(png_path)
    draw = ImageDraw.Draw(img)
    
    for i, room in enumerate(rooms):
        bbox = room['bbox']
        draw.rectangle(bbox, outline="red", width=3)
    
    img.save(output_path)
    print(f"Detected {len(rooms)} rooms")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python png_based_detection.py <png_path> <output_path>")
        sys.exit(1)
    
    png_path = sys.argv[1]
    output_path = sys.argv[2]
    
    print("Attempting PNG-based room detection...")
    rooms = simple_wall_based_detection(png_path)
    
    if rooms:
        visualize_rooms(png_path, rooms, output_path)
    else:
        print("No rooms detected. The PNG-based approach may need tuning.")

