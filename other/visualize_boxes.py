#!/usr/bin/env python3
"""
Visualize extracted bounding boxes on blueprint images.
Creates annotated images showing detected rooms.
"""

import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not installed. Install with: pip install Pillow")
    print("Visualization will be skipped.")

def draw_bounding_boxes(image_path, rooms_data, output_path):
    """Draw bounding boxes on an image."""
    if not HAS_PIL:
        print("PIL not available, skipping visualization")
        return False
    
    try:
        # Load image
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, fallback to default if not available
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except:
            font = ImageFont.load_default()
        
        # Draw each bounding box
        for room in rooms_data.get('rooms', []):
            bbox = room['bounding_box']
            x_min, y_min, x_max, y_max = bbox
            
            # Scale coordinates from 0-1000 to image dimensions
            img_width, img_height = img.size
            x1 = int((x_min / 1000) * img_width)
            y1 = int((y_min / 1000) * img_height)
            x2 = int((x_max / 1000) * img_width)
            y2 = int((y_max / 1000) * img_height)
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
            
            # Add room label
            label = room.get('name_hint', room.get('id', ''))
            if label:
                # Draw text background
                text_bbox = draw.textbbox((x1, y1 - 20), label, font=font)
                draw.rectangle(text_bbox, fill="red", outline="red")
                draw.text((x1, y1 - 20), label, fill="white", font=font)
        
        # Save annotated image
        img.save(output_path)
        return True
    except Exception as e:
        print(f"Error visualizing {image_path}: {e}", file=sys.stderr)
        return False

def visualize_sample(sample_dir, output_dir):
    """Visualize bounding boxes for a sample."""
    sample_path = Path(sample_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find JSON file (from extract_rooms_from_svg.py output)
    json_file = None
    for f in output_dir.glob("*_rooms.json"):
        if sample_path.name in str(f):
            json_file = f
            break
    
    if not json_file:
        # Try to extract rooms directly
        svg_path = sample_path / "model.svg"
        if not svg_path.exists():
            print(f"No SVG found in {sample_path}")
            return False
        
        # Extract rooms
        import subprocess
        result = subprocess.run(
            ['python3', 'extract_rooms_from_svg.py', str(svg_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print(f"Error extracting rooms: {result.stderr}")
            return False
        
        # Parse JSON from output
        import json as json_lib
        rooms_data = json_lib.loads(result.stdout)
    else:
        with open(json_file, 'r') as f:
            rooms_data = json.load(f)
    
    # Find PNG image
    png_scaled = sample_path / "F1_scaled.png"
    png_original = sample_path / "F1_original.png"
    png_path = png_scaled if png_scaled.exists() else png_original
    
    if not png_path.exists():
        print(f"No PNG found in {sample_path}")
        return False
    
    # Create visualization
    output_path = output_dir / f"{sample_path.name}_annotated.png"
    success = draw_bounding_boxes(png_path, rooms_data, output_path)
    
    if success:
        print(f"✓ Created visualization: {output_path}")
        print(f"  Detected {rooms_data.get('total_rooms', 0)} rooms")
    
    return success

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python visualize_boxes.py <sample_directory> <output_directory>")
        print("\nExample:")
        print("  python visualize_boxes.py /path/to/sample/3954 test_output/")
        sys.exit(1)
    
    sample_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    visualize_sample(sample_dir, output_dir)

