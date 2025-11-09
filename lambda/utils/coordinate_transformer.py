"""
Coordinate transformation utilities for Lambda function.
Handles transformation from pixel coordinates to normalized 0-1000 range.
"""


def transform_coordinates_to_normalized(
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
    image_width: int,
    image_height: int
) -> tuple:
    """
    Transform bounding box coordinates from pixel space to normalized 0-1000 range.
    
    Args:
        x_min: Minimum x coordinate in pixels
        y_min: Minimum y coordinate in pixels
        x_max: Maximum x coordinate in pixels
        y_max: Maximum y coordinate in pixels
        image_width: Original image width in pixels
        image_height: Original image height in pixels
        
    Returns:
        Tuple of (x_min_norm, y_min_norm, x_max_norm, y_max_norm) in 0-1000 range
    """
    # Normalize to 0-1 range first
    x_min_norm = x_min / image_width
    y_min_norm = y_min / image_height
    x_max_norm = x_max / image_width
    y_max_norm = y_max / image_height
    
    # Scale to 0-1000 range
    x_min_1000 = int(x_min_norm * 1000)
    y_min_1000 = int(y_min_norm * 1000)
    x_max_1000 = int(x_max_norm * 1000)
    y_max_1000 = int(y_max_norm * 1000)
    
    # Ensure values are within 0-1000 range
    x_min_1000 = max(0, min(1000, x_min_1000))
    y_min_1000 = max(0, min(1000, y_min_1000))
    x_max_1000 = max(0, min(1000, x_max_1000))
    y_max_1000 = max(0, min(1000, y_max_1000))
    
    return (x_min_1000, y_min_1000, x_max_1000, y_max_1000)


def transform_bounding_box(
    bounding_box: list,
    original_width: int,
    original_height: int,
    resized_width: int = 640,
    resized_height: int = 640
) -> list:
    """
    Transform bounding box from resized image coordinates back to original image coordinates,
    then normalize to 0-1000 range.
    
    Note: Since SageMaker endpoint already returns normalized 0-1000 coordinates,
    this function is mainly for reference if we need to handle coordinate transformation
    in Lambda instead of SageMaker.
    
    Args:
        bounding_box: List of [x_min, y_min, x_max, y_max] in resized image coordinates
        original_width: Original image width
        original_height: Original image height
        resized_width: Resized image width (default 640)
        resized_height: Resized image height (default 640)
        
    Returns:
        List of [x_min, y_min, x_max, y_max] in normalized 0-1000 range
    """
    x_min_resized, y_min_resized, x_max_resized, y_max_resized = bounding_box
    
    # Calculate scaling factor (assuming aspect ratio was maintained with padding)
    scale = min(resized_width / original_width, resized_height / original_height)
    
    # Calculate padding offsets
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    pad_x = (resized_width - new_width) // 2
    pad_y = (resized_height - new_height) // 2
    
    # Transform back to original image coordinates
    x_min_original = (x_min_resized - pad_x) / scale
    y_min_original = (y_min_resized - pad_y) / scale
    x_max_original = (x_max_resized - pad_x) / scale
    y_max_original = (y_max_resized - pad_y) / scale
    
    # Normalize to 0-1000 range
    return list(transform_coordinates_to_normalized(
        x_min_original, y_min_original,
        x_max_original, y_max_original,
        original_width, original_height
    ))

