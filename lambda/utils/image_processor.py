"""
Image preprocessing utilities for Lambda function.
Handles image resizing and normalization for YOLOv8 model input.
"""

import io
from PIL import Image
import numpy as np


def resize_image(image: Image.Image, target_size: tuple = (640, 640)) -> Image.Image:
    """
    Resize image to target size while maintaining aspect ratio.
    Adds padding if necessary to maintain aspect ratio.
    
    Args:
        image: PIL Image object
        target_size: Tuple of (width, height) for target size
        
    Returns:
        Resized PIL Image with padding if needed
    """
    target_width, target_height = target_size
    original_width, original_height = image.size
    
    # Calculate scaling factor to fit image within target size
    scale = min(target_width / original_width, target_height / original_height)
    
    # Calculate new dimensions
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    
    # Resize image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create new image with target size and paste resized image centered
    result_image = Image.new('RGB', target_size, (255, 255, 255))  # White background
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    result_image.paste(resized_image, (paste_x, paste_y))
    
    return result_image


def normalize_image(image: Image.Image) -> np.ndarray:
    """
    Normalize image pixel values from 0-255 to 0-1 range.
    
    Args:
        image: PIL Image object
        
    Returns:
        Normalized numpy array
    """
    # Convert PIL Image to numpy array
    img_array = np.array(image, dtype=np.float32)
    
    # Normalize to 0-1 range
    img_array = img_array / 255.0
    
    return img_array


def preprocess_image(image_bytes: bytes, target_size: tuple = (640, 640)) -> Image.Image:
    """
    Complete preprocessing pipeline: load, resize, and prepare image for inference.
    
    Args:
        image_bytes: Raw image bytes
        target_size: Target size tuple (width, height)
        
    Returns:
        Preprocessed PIL Image ready for inference
    """
    # Load image from bytes
    image = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to target size
    resized_image = resize_image(image, target_size)
    
    return resized_image


def get_image_dimensions(image_bytes: bytes) -> tuple:
    """
    Get original image dimensions without full preprocessing.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Tuple of (width, height)
    """
    image = Image.open(io.BytesIO(image_bytes))
    return image.size

