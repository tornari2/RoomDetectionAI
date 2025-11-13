#!/usr/bin/env python3
"""
SageMaker inference script for YOLOv8 room detection model.
Handles model loading, image preprocessing, inference, and response formatting.
"""

import json
import os
import sys
import time
import base64
import numpy as np
from pathlib import Path

import torch
from ultralytics import YOLO
from PIL import Image
import io


def model_fn(model_dir):
    """
    Load the model for inference.
    This function is called once when the endpoint starts.
    """
    print(f"Loading model from {model_dir}")
    
    # Find model file
    model_path = Path(model_dir) / "model.pt"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load YOLOv8 model WITHOUT validation
    # Use task='detect' to skip dataset validation
    model = YOLO(str(model_path), task='detect')
    model.to('cpu')  # Serverless inference uses CPU
    
    print("Model loaded successfully")
    return model


def input_fn(request_body, request_content_type):
    """
    Deserialize and prepare the prediction input.
    """
    if request_content_type == 'application/json':
        # JSON input with base64 encoded image
        input_data = json.loads(request_body)
        
        if 'image' in input_data:
            # Decode base64 image
            image_data = base64.b64decode(input_data['image'])
            image = Image.open(io.BytesIO(image_data))
            return image
        elif 'image_url' in input_data:
            # Load from URL (S3 URL)
            import urllib.request
            with urllib.request.urlopen(input_data['image_url']) as response:
                image_data = response.read()
            image = Image.open(io.BytesIO(image_data))
            return image
        else:
            raise ValueError("Input must contain 'image' (base64) or 'image_url'")
    
    elif request_content_type == 'image/jpeg' or request_content_type == 'image/png':
        # Direct image binary
        image = Image.open(io.BytesIO(request_body))
        return image
    
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")


def predict_fn(input_data, model):
    """
    Perform prediction on the deserialized input.
    """
    print("Running inference...")
    start_time = time.time()
    
    # Get image dimensions BEFORE inference
    img_width, img_height = input_data.size
    
    # Run YOLOv8 inference
    results = model(input_data, conf=0.25, iou=0.45, imgsz=640)
    
    inference_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Extract detections
    detections = []
    if len(results) > 0 and results[0].boxes is not None:
        boxes = results[0].boxes
        
        for i, box in enumerate(boxes):
            # Get box coordinates (normalized 0-1)
            xyxy = box.xyxy[0].cpu().numpy()
            confidence = float(box.conf[0].cpu().numpy())
            
            # Convert from pixel coordinates to normalized 0-1000 range
            # Format: [x_min, y_min, x_max, y_max]
            x_min = int((xyxy[0] / img_width) * 1000)
            y_min = int((xyxy[1] / img_height) * 1000)
            x_max = int((xyxy[2] / img_width) * 1000)
            y_max = int((xyxy[3] / img_height) * 1000)
            
            # Ensure values are within 0-1000 range
            x_min = max(0, min(1000, x_min))
            y_min = max(0, min(1000, y_min))
            x_max = max(0, min(1000, x_max))
            y_max = max(0, min(1000, y_max))
            
            detections.append({
                "id": f"room_{i+1:03d}",
                "bounding_box": [x_min, y_min, x_max, y_max],
                "confidence": round(confidence, 4)
            })
    
    print(f"Inference completed in {inference_time:.2f}ms")
    print(f"Detected {len(detections)} rooms")
    
    return {
        "detections": detections,
        "inference_time_ms": round(inference_time, 2),
        "image_size": [img_width, img_height]
    }


def output_fn(prediction, content_type):
    """
    Serialize the prediction result.
    """
    if content_type == 'application/json':
        # Format response according to API spec
        response = {
            "status": "success",
            "processing_time_ms": prediction["inference_time_ms"],
            "detected_rooms": prediction["detections"]
        }
        return json.dumps(response)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

