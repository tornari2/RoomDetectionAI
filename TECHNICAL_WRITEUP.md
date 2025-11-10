# Room Detection AI - Technical Writeup

## Executive Summary

This document outlines the technical methodology, model architecture decisions, and data preparation processes employed in developing a YOLOv8-based room detection system for architectural blueprint analysis. The system achieves real-time room boundary detection with high accuracy across diverse blueprint styles.

---

## 1. Methodology Overview

### 1.1 Problem Statement
Automated detection and segmentation of rooms in architectural blueprints presents unique challenges:
- Variable blueprint quality and resolution
- Diverse architectural styles and notation systems
- Complex room shapes and overlapping boundaries
- Need for real-time inference capabilities

### 1.2 Solution Architecture
We implemented a serverless, cloud-native architecture leveraging:
- **AWS Lambda** for request handling and preprocessing
- **AWS SageMaker** for model hosting and inference
- **Amazon S3** for blueprint storage
- **DynamoDB** for status tracking and metadata
- **React-based frontend** for user interaction

---

## 2. Model Selection and Rationale

### 2.1 YOLOv8 Architecture
**Selection Criteria:**
- **Real-time performance**: Sub-second inference times required for production use
- **Object detection capabilities**: Native support for bounding box prediction
- **Transfer learning**: Pre-trained on COCO dataset provides strong foundational features
- **Resource efficiency**: Optimized for deployment on CPU and GPU infrastructure

**Model Specifications:**
- **Base Model**: YOLOv8n (Nano variant)
- **Input Resolution**: 640x640 pixels
- **Framework**: Ultralytics YOLOv8
- **Inference Backend**: PyTorch

### 2.2 Architecture Advantages
- **Single-stage detection**: Eliminates need for region proposal networks
- **Anchor-free design**: Simplifies training and improves generalization
- **Feature pyramid networks**: Captures multi-scale room features
- **CSPNet backbone**: Efficient feature extraction with reduced parameters

### 2.3 Alternative Approaches Considered
| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Mask R-CNN | Precise segmentation | Slower inference, heavier | Rejected |
| RetinaNet | Good accuracy | Slower than YOLO | Rejected |
| Traditional CV | No training required | Poor generalization | Rejected |
| Custom CNN | Full control | Requires more data | Future work |

---

## 3. Data Preparation Process

### 3.1 Dataset Composition
**Source Data:**
- 5,992 architectural blueprint images
- Diverse sources: residential, commercial, mixed-use buildings
- Multiple architectural styles and scales
- Various image qualities (scanned, digital, CAD exports)

**Dataset Split:**
- Training: 70% (4,194 images)
- Validation: 6.7% (400 images)
- Test: 6.7% (398 images)
- Reserved: 16.6% (1,000 images for future fine-tuning)

### 3.2 Annotation Methodology

**Phase 1: Automated Labeling**
```python
# SVG-based room extraction
rooms = extract_rooms_from_svg(blueprint_svg)
for room in rooms:
    bounding_box = calculate_bbox(room.polygon)
    confidence = verify_room_validity(room)
```

**Phase 2: Hybrid Verification**
- PNG-based detection for quality control
- Manual verification of edge cases
- Offset correction for alignment issues
- Duplicate detection and removal

**Phase 3: Format Conversion**
```bash
# COCO to YOLO format conversion
python coco_to_yolo.py \
  --coco-dir data/annotations \
  --output-dir data/yolo_labels \
  --split train,val,test
```

### 3.3 Data Augmentation Strategy
To improve model robustness, we applied:
- **Geometric transforms**: Rotation (±15°), scaling (0.8-1.2x), translation (±10%)
- **Color jittering**: Brightness, contrast, saturation adjustments
- **Noise injection**: Gaussian noise to simulate scan artifacts
- **Mosaic augmentation**: 4-image composition for multi-scale learning

### 3.4 Quality Assurance
**Validation Metrics:**
- Annotation accuracy: Manual review of 10% sample (>95% accuracy)
- Bounding box alignment: Automated IoU verification (>0.85 threshold)
- Class distribution analysis: Ensured balanced representation
- Edge case coverage: Included L-shaped, irregular, and small rooms

---

## 4. Model Training

### 4.1 Training Configuration
```yaml
model: yolov8n.pt
data: dataset.yaml
epochs: 100
batch_size: 16
img_size: 640
optimizer: AdamW
learning_rate: 0.001
weight_decay: 0.0005
```

### 4.2 Training Infrastructure
- **Platform**: AWS SageMaker Training Jobs
- **Instance Type**: ml.g4dn.xlarge (GPU-accelerated)
- **Framework**: PyTorch 2.0 with CUDA 11.8
- **Training Time**: ~4 hours for 100 epochs
- **Checkpointing**: Best model saved based on validation mAP

### 4.3 Hyperparameter Tuning
Conducted grid search over:
- Learning rate: [0.0001, 0.001, 0.01]
- Batch size: [8, 16, 32]
- Image size: [416, 512, 640]
- Data augmentation intensity: [low, medium, high]

**Optimal Configuration:**
- Learning rate: 0.001
- Batch size: 16
- Image size: 640
- Augmentation: Medium intensity

---

## 5. Deployment Architecture

### 5.1 Inference Pipeline
```
User Upload → API Gateway → Lambda (preprocessing) 
→ SageMaker Endpoint → Lambda (postprocessing) 
→ DynamoDB (storage) → Frontend (display)
```

### 5.2 CPU vs GPU Deployment Decision
**Analysis Results:**
- **CPU (ml.m5.large)**: 150-300ms inference time
- **GPU (ml.g4dn.xlarge)**: 50-100ms inference time
- **Cost differential**: 3x higher for GPU
- **Decision**: CPU deployment for cost efficiency at acceptable latency

### 5.3 Preprocessing Pipeline
```python
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    # Load image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Resize to model input size
    image = image.resize((640, 640), Image.LANCZOS)
    
    # Normalize pixel values
    image_array = np.array(image) / 255.0
    
    # Convert to model format
    return image_array.transpose(2, 0, 1)
```

### 5.4 Postprocessing and Coordinate Transformation
```python
def transform_coordinates(bbox, original_size, model_size=(640, 640)):
    # Denormalize from model coordinates
    x1, y1, x2, y2 = bbox
    
    # Scale to original image dimensions
    scale_x = original_size[0] / model_size[0]
    scale_y = original_size[1] / model_size[1]
    
    return [
        int(x1 * scale_x),
        int(y1 * scale_y),
        int(x2 * scale_x),
        int(y2 * scale_y)
    ]
```

---

## 6. Performance Metrics

### 6.1 Model Performance
| Metric | Value |
|--------|-------|
| mAP@0.5 | 0.847 |
| mAP@0.5:0.95 | 0.612 |
| Precision | 0.831 |
| Recall | 0.798 |
| F1 Score | 0.814 |

### 6.2 Inference Performance
- **Average latency**: 220ms (CPU)
- **P95 latency**: 380ms
- **Throughput**: ~4.5 requests/second per instance
- **Cold start time**: 2.5s (Lambda + SageMaker)

### 6.3 Error Analysis
**Common failure modes:**
- Small rooms (<5% of image area): Lower detection rate
- Overlapping spaces: Occasional boundary confusion
- Non-standard shapes: Reduced confidence scores
- Low-quality scans: Increased false negatives

---

## 7. Future Improvements

### 7.1 Model Enhancements
- **Room classification**: Add semantic labels (bedroom, kitchen, bathroom)
- **Instance segmentation**: Mask R-CNN for precise boundaries
- **Multi-floor support**: Detect and separate floor levels
- **Confidence calibration**: Improve probability estimates

### 7.2 Data Expansion
- Increase dataset to 10,000+ annotated blueprints
- Include international architectural standards
- Add temporal data (blueprint revisions)
- Incorporate 3D floor plan data

### 7.3 System Optimizations
- Model quantization for faster CPU inference
- Batch processing for multiple blueprints
- Real-time feedback during upload
- Progressive result refinement

---

## 8. Conclusion

The implemented YOLOv8-based room detection system demonstrates strong performance across diverse blueprint types while maintaining real-time inference capabilities. The serverless architecture provides scalability and cost efficiency, making it suitable for production deployment. Continuous improvement through expanded training data and model refinement will further enhance detection accuracy and robustness.

**Key Achievements:**
- ✅ Sub-second inference on CPU infrastructure
- ✅ 84.7% mAP@0.5 detection accuracy
- ✅ Fully automated, scalable deployment
- ✅ Production-ready web interface
- ✅ Comprehensive API with status tracking

**Repository**: [github.com/tornari2/RoomDetectionAI](https://github.com/tornari2/RoomDetectionAI)

**Technology Stack**: YOLOv8, PyTorch, AWS Lambda, SageMaker, React, TypeScript

---

*Document Version: 1.0*  
*Last Updated: November 10, 2025*

