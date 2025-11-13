#!/usr/bin/env python3
"""
Wall detection and bounding box snapping using PIL and numpy only.
Detects walls by analyzing dark horizontal/vertical lines and snaps bounding boxes.
"""

import numpy as np
from PIL import Image
from pathlib import Path

def detect_walls_pil(image_path, wall_threshold=50, min_wall_length=0.1):
    """
    Detect wall positions in blueprint image using PIL and numpy.
    Returns horizontal and vertical wall positions.
    
    Args:
        image_path: Path to PNG image
        wall_threshold: Pixel value threshold for walls (0-255, lower = darker)
        min_wall_length: Minimum fraction of image dimension for a wall
    """
    # Load image
    img = Image.open(image_path)
    img_array = np.array(img.convert('L'))  # Convert to grayscale
    height, width = img_array.shape
    
    # Threshold: walls are dark (low pixel values)
    wall_mask = img_array < wall_threshold
    
    # Detect horizontal walls
    h_walls = []
    for y in range(height):
        # Count wall pixels in this row
        wall_pixels = np.sum(wall_mask[y, :])
        if wall_pixels > width * min_wall_length:
            h_walls.append(y)
    
    # Detect vertical walls
    v_walls = []
    for x in range(width):
        # Count wall pixels in this column
        wall_pixels = np.sum(wall_mask[:, x])
        if wall_pixels > height * min_wall_length:
            v_walls.append(x)
    
    # Group nearby walls (within 3 pixels) to get wall centers
    def group_walls(walls, threshold=3):
        if not walls:
            return []
        
        grouped = []
        current_group = [walls[0]]
        
        for w in walls[1:]:
            if w - current_group[-1] <= threshold:
                current_group.append(w)
            else:
                grouped.append(int(np.mean(current_group)))
                current_group = [w]
        
        if current_group:
            grouped.append(int(np.mean(current_group)))
        
        return grouped
    
    h_walls_grouped = group_walls(h_walls)
    v_walls_grouped = group_walls(v_walls)
    
    return sorted(h_walls_grouped), sorted(v_walls_grouped)

def snap_to_wall(value, wall_positions, snap_threshold=15):
    """
    Snap a coordinate value to the nearest wall position if within threshold.
    """
    if not wall_positions:
        return value
    
    # Find nearest wall
    nearest_wall = min(wall_positions, key=lambda w: abs(w - value))
    
    # Snap if within threshold
    if abs(nearest_wall - value) <= snap_threshold:
        return nearest_wall
    
    return value

def snap_bbox_to_walls(bbox, h_walls, v_walls, snap_threshold=15):
    """
    Snap bounding box edges to nearest walls.
    bbox: [x_min, y_min, x_max, y_max]
    Returns snapped bbox.
    """
    x_min, y_min, x_max, y_max = bbox
    
    # Snap left and right edges to vertical walls
    x_min = snap_to_wall(x_min, v_walls, snap_threshold)
    x_max = snap_to_wall(x_max, v_walls, snap_threshold)
    
    # Snap top and bottom edges to horizontal walls
    y_min = snap_to_wall(y_min, h_walls, snap_threshold)
    y_max = snap_to_wall(y_max, h_walls, snap_threshold)
    
    # Ensure valid bbox
    if x_max <= x_min:
        x_max = x_min + 1
    if y_max <= y_min:
        y_max = y_min + 1
    
    return [x_min, y_min, x_max, y_max]

if __name__ == "__main__":
    # Test on a sample image
    test_image = "/Users/michaeltornaritis/Downloads/archive/cubicasa5k/cubicasa5k/high_quality/3954/F1_scaled.png"
    h_walls, v_walls = detect_walls_pil(test_image)
    print(f"Detected {len(h_walls)} horizontal walls, {len(v_walls)} vertical walls")
    if h_walls:
        print(f"Sample horizontal walls: {h_walls[:10]}")
    if v_walls:
        print(f"Sample vertical walls: {v_walls[:10]}")
