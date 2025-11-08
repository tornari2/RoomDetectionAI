# Product Requirements Document (PRD): Location Detection AI
## Innergy Gauntlet Project

---

## 1. Executive Summary

### 1.1 Project Overview
The Location Detection AI is a proof-of-concept service designed to automatically detect and extract room boundaries from architectural blueprints, eliminating the manual tracing process currently required by Innergy users (architects and contractors).

### 1.2 Project Goal
Build an AWS-hosted AI service that processes blueprint images and returns the bounding box coordinates of all detected rooms in under 30 seconds, demonstrating the technical feasibility of automating room boundary detection.

### 1.3 Success Criteria
- **Primary:** Successfully detect and return bounding boxes for rooms in public domain blueprint samples
- **Secondary:** Process blueprints in <30 seconds with visually accurate room detection
- **Demo Impact:** Create a compelling demonstration showing automated room detection vs. manual tracing

---

## 2. Problem Statement & Context

### 2.1 Current State
Innergy users (architects and contractors) spend significant time manually tracing room boundaries on architectural blueprints using 2D CAD tools. For a typical 10-room floor plan, this process takes approximately 5 minutes of tedious clicking and boundary definition.

### 2.2 Proposed Solution
An AI-powered service that automatically analyzes blueprint images and outputs the coordinates of detected room boundaries, reducing the 5-minute manual process to under 30 seconds of automated processing.

### 2.3 Business Value
- **User Efficiency:** 90%+ time savings on room boundary definition
- **Competitive Advantage:** Major differentiator for sales and market positioning
- **User Experience:** Transform tedious manual task into instant automated process

---

## 3. User Personas & Use Cases

### 3.1 Primary Users
**Residential Architects & Contractors**
- Upload residential floor plans (most common use case)
- Need quick turnaround for multiple projects
- Value accuracy over speed, but need both

**Commercial/Industrial Users** (Secondary)
- Larger, more complex blueprints
- May have mixed-use spaces

### 3.2 Core User Journey
1. User uploads blueprint image (PNG/JPG) via drag & drop or file browser
2. System processes blueprint and detects rooms, hallways, entryways, and foyers
3. User views automatically-generated room boundaries overlaid on blueprint visualization
4. User exports annotated image (PNG with bounding boxes) and/or JSON coordinates
5. *(Future)* User manually adjusts boundaries if needed

---

## 4. Functional Requirements

### 4.1 Core Capabilities (MUST HAVE)

#### FR-1: Blueprint Upload
- **Input Formats:** PNG, JPG (PDF support removed for MVP simplicity)
- **Upload Method:** Web-based file upload via React interface
  - Drag & drop support
  - File browser button (alternative to drag & drop)
- **File Size:** Support typical blueprint sizes (recommend 50MB max for MVP)

#### FR-2: Room Detection Processing
- **Processing Time:** <30 seconds per blueprint (hard requirement)
- **Detection Scope:** Identify enclosed spaces that represent rooms
- **Output Format:** Bounding boxes (rectangular coordinates)
- **Coordinate System:** Normalized 0-1000 range `[x_min, y_min, x_max, y_max]`

#### FR-3: Result Visualization
- **Display:** Overlay detected bounding boxes on original blueprint in React UI
- **Visual Feedback:** Clear indication of detected room boundaries
  - React front-end renders the automatically-created room boundaries on the blueprint visualization
  - Bounding boxes displayed as colored rectangles overlaid on image
- **Export Options:**
  - Export annotated image: Download PNG file with bounding boxes rendered
  - Export JSON: Download JSON file containing room coordinates and metadata

#### FR-4: API Response Structure
```json
{
  "blueprint_id": "unique_identifier",
  "processing_time_ms": 15420,
  "detected_rooms": [
    {
      "id": "room_001",
      "bounding_box": [50, 50, 200, 300],
      "confidence": 0.95
    },
    {
      "id": "room_002",
      "bounding_box": [250, 50, 700, 500],
      "confidence": 0.92
    }
  ],
  "status": "success"
}
```

**Note:** Room name hints moved to future enhancements (see Section 13).

### 4.2 Edge Case Handling

#### Irregular Rooms
- Inscribe irregular/curved rooms within rectangular bounding boxes
- Accept reduced precision for non-rectangular spaces

#### Unidentifiable Spaces
- Label ambiguous spaces as "Unknown"
- Return bounding box with low confidence score

#### Open Floor Plans
- Attempt to detect logical room divisions based on furniture layout or partial walls
- If no clear boundaries exist, return single large bounding box

#### Multiple Floors
- For MVP, process as single combined space
- *(Future enhancement: floor detection)*

---

## 5. Technical Architecture

### 5.1 System Components

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   React     │  HTTP   │   AWS API        │   ML    │   AWS AI/ML     │
│  Frontend   │ ──────> │   Gateway +      │ ──────> │   Services      │
│             │         │   Lambda         │         │                 │
└─────────────┘         └──────────────────┘         └─────────────────┘
                               │                              │
                               │                              │
                               v                              v
                        ┌──────────────────┐         ┌─────────────────┐
                        │   S3 Bucket      │         │   SageMaker or  │
                        │   (Blueprints)   │         │   Textract      │
                        └──────────────────┘         └─────────────────┘
```

### 5.2 Technology Stack (MUST USE)

#### Cloud Platform
- **Provider:** AWS (Mandatory)
- **Region:** us-east-1
- **Compliance:** None required for MVP

#### Core AWS Services (Required)
- **Amazon S3:** Blueprint storage and training data storage
- **AWS Lambda:** Serverless processing orchestration and image preprocessing
- **Amazon API Gateway:** REST API endpoint with async processing support
- **Amazon SageMaker:** 
  - Custom container for YOLOv8 model training
  - Serverless Inference endpoint for model deployment
- **Amazon CloudWatch:** Logging and monitoring

#### Development Stack
- **Frontend:** React (TypeScript recommended)
- **Backend Logic:** Python 3.9+ (Lambda runtime)
- **IDE:** Visual Studio Code
- **Version Control:** Git/GitHub

### 5.3 AI/ML Approach: Fine-Tuned YOLOv8 Object Detection Model

#### Primary Approach: YOLOv8 Custom Training on SageMaker

**Model Selection:**
- **Model:** YOLOv8s (You Only Look Once version 8 - Small variant)
- **Architecture:** State-of-the-art object detection model (2023)
- **Training Platform:** Amazon SageMaker with custom container
- **Deployment:** SageMaker Serverless Inference endpoint
- **Training Time:** 2-4 hours for ~1000 images (ml.g4dn.xlarge instance)
- **Model Size:** ~22 MB

**Training Pipeline:**
1. **Data Preparation:**
   - Source: Pre-annotated residential floor plan images in COCO format (4,200 train images)
   - Pre-labeled annotations: Use existing COCO format annotations from `cubicasa5k_coco` directory
   - Format: Convert COCO annotations to YOLO format using `coco_to_yolo.py` script
   - Split: Pre-existing train/val/test splits in COCO JSON files
   - **Time Savings:** Pre-annotated data eliminates 10-15+ hours of manual labeling work

2. **Model Training:**
   - Deploy YOLOv8 in custom SageMaker container
   - Fine-tune on labeled blueprint dataset
   - Hyperparameter tuning for optimal accuracy
   - Validation on held-out test set

3. **Deployment:**
   - Deploy trained model to SageMaker Serverless Inference endpoint
   - Endpoint auto-scales to zero when idle (cost-efficient)
   - Cold start: 3-5 seconds (only when endpoint scales up from zero)
   - Warm inference: ~100-500ms per blueprint

**Advantages:**
- ✅ High accuracy on domain-specific data
- ✅ Fast inference (<30 seconds total processing time)
- ✅ Handles irregular rooms and complex layouts
- ✅ Built-in confidence scores
- ✅ State-of-the-art model architecture

**Data Requirements:**
- Training data: Pre-annotated residential floor plan images in COCO format
- Pre-labeled annotations: Dataset includes pre-validated COCO format annotations (no manual labeling required)
- Annotation format: COCO format with room bounding boxes already aligned to images
- Validation: Pre-validated annotations from dataset creators

---

## 6. Data Requirements

### 6.1 Training/Testing Data

#### Dataset Source
- **Format:** Cubicasa5k dataset with **pre-annotated COCO format** annotations
- **File Types:** PNG images with corresponding COCO JSON annotation files
- **Content:** Residential architectural floor plans
- **Annotation Source:** Pre-existing COCO format annotations in `cubicasa5k_coco` directory
- **Image Selection:** Use **F1_original.png** images (referenced in COCO annotations)
- **Dataset Size:** 
  - **Train set:** 4,200 images with room annotations
  - **Validation set:** ~400 images (based on val_coco_pt.json)
  - **Test set:** ~400 images (based on test_coco_pt.json)
- **Folder Distribution (Train Set):**
  - `high_quality`: 825 images (19.6%)
  - `high_quality_architectural`: 3,217 images (76.6%)
  - `colorful`: 158 images (3.8%)
- **Rationale:** Using all folders provides 5x more training data (4,200 vs 825). COCO annotations are pre-validated and eliminate coordinate alignment issues. Including varied styles improves model robustness.

#### Data Labeling Strategy

**Pre-Annotated COCO Format:**
- Dataset includes pre-existing COCO format annotations (`train_coco_pt.json`, `val_coco_pt.json`, `test_coco_pt.json`)
- Annotations contain room bounding boxes already aligned to PNG images
- **Categories:** `wall` (ID 1), `room` (ID 2) - using room annotations only
- **Bounding Box Format:** COCO format `[x, y, width, height]` (top-left corner + dimensions)
- **Advantages:**
  - ✅ Eliminates SVG parsing complexity and coordinate transformation issues
  - ✅ Pre-validated annotations from dataset creators
  - ✅ No manual labeling required (saves 10-15+ hours)
  - ✅ Consistent format across all samples
  - ✅ Already split into train/val/test sets

**Conversion to YOLO Format:**
- Convert COCO annotations to YOLO format using `coco_to_yolo.py` script
- **Training Format:** YOLO format (class_id, center_x, center_y, width, height - normalized 0-1)
- **Output Format:** Normalized coordinates 0-1000 `[x_min, y_min, x_max, y_max]` (for API response)
- Conversion process: COCO `[x, y, w, h]` → YOLO `[center_x, center_y, width, height]` (normalized)

#### Data Split Strategy
- **Use existing COCO splits:** 
  - `train_coco_pt.json`: 4,200 images
  - `val_coco_pt.json`: ~400 images  
  - `test_coco_pt.json`: ~400 images
- Split ratio: ~84% train / 8% val / 8% test
- All splits include images from all three folders (high_quality, high_quality_architectural, colorful)

### 6.2 Image Preprocessing

**Before Model Inference:**
1. **Resize:** Resize input image to model input size (640x640 for YOLOv8)
2. **Normalize Pixel Values:** Normalize pixel values from 0-255 to 0-1 range (standard for YOLOv8)
3. **Maintain Aspect Ratio:** Preserve aspect ratio during resizing with padding if needed

**Note:** Coordinate normalization to 0-1000 range occurs in Lambda function during response transformation, not during image preprocessing.

### 6.3 Data Processing Pipeline (Inference)

1. User uploads blueprint image (PNG/JPG) via React frontend
2. Image stored in S3 bucket
3. Lambda function triggered via API Gateway
4. Lambda retrieves image from S3
5. Lambda preprocesses image (resize, normalize)
6. Lambda invokes SageMaker Serverless Inference endpoint
7. YOLOv8 model returns bounding boxes with confidence scores
8. Lambda transforms coordinates from pixel space to normalized 0-1000 range
9. Lambda formats response and returns to frontend
10. React displays bounding boxes overlaid on blueprint

---

## 7. Non-Functional Requirements

### 7.1 Performance
- **Processing Time:** <30 seconds per blueprint (MANDATORY)
- **Target:** 10-20 seconds average for typical residential blueprints
- **API Response Time:** <2 seconds for non-processing requests

### 7.2 Scalability
- **MVP Volume:** Single-user testing, ~10-50 blueprints total
- **Architecture:** Design for future scale (serverless = auto-scaling)

### 7.3 Reliability
- **Error Handling:** Graceful failures with clear error messages
- **Retry Logic:** Implement basic retry for transient failures
- **Logging:** CloudWatch logs for debugging

### 7.4 Security
- **API Access:** Simple API key authentication (sufficient for demo)
- **Data Privacy:** Blueprints stored temporarily in S3, auto-delete after 24 hours
- **HTTPS:** All API calls over HTTPS

### 7.5 Usability
- **UI/UX:** Clean, intuitive React interface
- **Feedback:** Loading indicators during processing
- **Visualization:** Clear overlay of detected rooms on blueprint

---

## 8. API Specifications

### 8.1 Processing Model: Asynchronous with Polling

**Architecture:**
- Processing is asynchronous to handle <30 second requirement
- Frontend polls status endpoint every 2-3 seconds
- Status updates from "processing" → "completed" or "failed"

### 8.2 Endpoints

#### POST /api/v1/blueprints/upload
**Purpose:** Upload blueprint and initiate processing

**Request:**
```
POST /api/v1/blueprints/upload
Content-Type: multipart/form-data

file: <blueprint_image>
```

**Response:**
```json
{
  "blueprint_id": "bp_abc123",
  "status": "processing",
  "message": "Blueprint uploaded successfully. Processing started."
}
```

**Behavior:**
- Immediately returns with `blueprint_id` and `status: "processing"`
- Processing begins asynchronously in background
- Frontend should begin polling `/status` endpoint

---

#### GET /api/v1/blueprints/{blueprint_id}/status
**Purpose:** Check processing status (polled by frontend)

**Response (Processing):**
```json
{
  "blueprint_id": "bp_abc123",
  "status": "processing",
  "message": "Analyzing blueprint..."
}
```

**Response (Completed):**
```json
{
  "blueprint_id": "bp_abc123",
  "status": "completed",
  "processing_time_ms": 15420,
  "detected_rooms": [
    {
      "id": "room_001",
      "bounding_box": [50, 50, 200, 300],
      "confidence": 0.95
    },
    {
      "id": "room_002",
      "bounding_box": [250, 50, 700, 500],
      "confidence": 0.92
    }
  ]
}
```

**Response (Failed):**
```json
{
  "blueprint_id": "bp_abc123",
  "status": "failed",
  "error": "processing_failed",
  "message": "Unable to detect clear room boundaries"
}
```

**Polling Strategy:**
- Frontend polls every 2-3 seconds
- Stop polling when status is "completed" or "failed"
- Maximum polling duration: 60 seconds (timeout)

---

#### GET /api/v1/blueprints/{blueprint_id}/results
**Purpose:** Retrieve final detected room coordinates (alternative to status endpoint)

**Response:**
```json
{
  "blueprint_id": "bp_abc123",
  "original_url": "https://s3.../blueprint.png",
  "detected_rooms": [
    {
      "id": "room_001",
      "bounding_box": [50, 50, 200, 300],
      "confidence": 0.95
    }
  ],
  "total_rooms": 15
}
```

**Note:** No limit on number of detected rooms. Confidence threshold filtering may be added later.

### 8.3 Error Responses
```json
{
  "error": "processing_failed",
  "message": "Unable to detect clear room boundaries",
  "blueprint_id": "bp_abc123",
  "details": "No enclosed spaces found in blueprint"
}
```

---

## 9. Development Phases & Milestones

### Phase 1: Foundation & Data Preparation (Week 1)
- [ ] Set up AWS account and configure services (AWS Console)
- [ ] Create basic React frontend with file upload
- [ ] Implement S3 upload functionality
- [ ] Set up API Gateway + Lambda skeleton
- [ ] **Data Preparation:**
  - [ ] Convert COCO format annotations to YOLO format using `coco_to_yolo.py`
  - [ ] Generate YOLO format label files for train/val/test sets
  - [ ] Verify image paths match COCO annotation file paths
  - [ ] Validate annotation quality (visual spot-checking of sample images)
  - [ ] Organize training/validation/test splits (already provided in COCO JSON files)

### Phase 2: Model Training (Week 2-3)
- [ ] Set up SageMaker environment
- [ ] Create custom container for YOLOv8
- [ ] Upload training data to S3
- [ ] Configure SageMaker training job
- [ ] Train YOLOv8 model on blueprint dataset
- [ ] Evaluate model performance on validation set
- [ ] Hyperparameter tuning if needed
- [ ] Deploy trained model to SageMaker Serverless Inference endpoint

### Phase 3: Backend Integration (Week 3-4)
- [ ] Implement Lambda function for image preprocessing
- [ ] Integrate Lambda with SageMaker endpoint
- [ ] Implement coordinate transformation (pixel → 0-1000 normalized)
- [ ] Set up async processing with status tracking
- [ ] Implement polling endpoint for status checks
- [ ] Error handling and edge cases
- [ ] Test end-to-end processing pipeline
- [ ] Optimize for <30 second processing requirement

### Phase 4: Frontend & Visualization (Week 4-5)
- [ ] Implement async polling in React frontend
- [ ] Implement bounding box overlay visualization
- [ ] Create export functionality (JSON download)
- [ ] Loading indicators and status feedback
- [ ] Error state handling in UI
- [ ] Polish user interface

### Phase 5: Demo Preparation (Week 5)
- [ ] Test with multiple blueprint samples
- [ ] Performance testing and optimization
- [ ] Record demo video
- [ ] Prepare technical writeup
- [ ] Document AWS service usage and configuration

---

## 10. Deliverables (Gauntlet Submission)

### 10.1 Required Submissions

#### 1. Code Repository (GitHub)
- **Contents:**
  - React frontend code (TypeScript)
  - Lambda function code (Python)
  - Model training scripts (YOLOv8 on SageMaker)
  - COCO to YOLO conversion scripts (`coco_to_yolo.py`, `coco_to_yolo_filtered.py`)
  - Visualization scripts for annotation validation (`visualize_coco_samples.py`, `compare_folders.py`)
  - README with setup instructions
- **Documentation:**
  - Architecture diagram
  - API documentation
  - Setup and deployment guide
  - Model training documentation
  - COCO annotation format guide

#### 2. Demo (Video or Live)
- **Duration:** 5-10 minutes
- **Content:**
  - Upload a mock blueprint via React interface
  - Show processing (< 30 seconds)
  - Display detected room boundaries overlaid on blueprint
  - Export coordinates as JSON
  - Brief walkthrough of the code/architecture

#### 3. Technical Writeup (1-2 pages)
- **Sections:**
  - Problem statement
  - Solution approach and methodology
  - AI/ML model choice and rationale
  - Data preparation process (COCO annotation conversion)
  - Challenges encountered and solutions
  - Performance metrics
  - Future improvements

#### 4. AWS AI/ML Services Documentation
- **Include:**
  - Specific AWS services used (Textract, SageMaker, etc.)
  - Configuration settings and parameters
  - Cost estimates for MVP usage
  - Rationale for service selection

### 10.2 Success Criteria for Gauntlet
- ✅ Working end-to-end demo (upload → process → visualize)
- ✅ Processing time <30 seconds
- ✅ Detects rooms in at least 2-3 different blueprint samples
- ✅ Clean, professional presentation
- ✅ Well-documented code and architecture
- ✅ Uses AWS services appropriately

---

## 11. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| AI accuracy insufficient for complex blueprints | High | Medium | Start with simple blueprints, clearly scope limitations, use auto-labeling for quality data |
| Processing time exceeds 30 seconds | High | Medium | Optimize model inference, use SageMaker Serverless Inference, reduce image resolution if needed |
| Difficulty finding training data | Low | Low | Auto-labeling from SVG structure eliminates manual labeling burden |
| AWS costs exceed budget | Low | Low | Use free tier, monitor spending, set billing alerts, use Serverless Inference (scales to zero) |
| Model training fails or underperforms | High | Medium | Start with smaller dataset, validate auto-generated labels, iterate on hyperparameters |
| Cold start delays in Serverless Inference | Medium | Low | Process multiple blueprints in same session, or switch to real-time endpoint for demo |

---

## 11. User Interface (UI) & User Experience (UX) Specifications

### 11.1 Technology Stack

- **Framework:** React with TypeScript
- **Styling:** CSS Modules or Tailwind CSS (recommended for rapid development)
- **Image Handling:** HTML5 Canvas API for bounding box overlay rendering
- **File Upload:** HTML5 File API with drag-and-drop support
- **State Management:** React Hooks (useState, useEffect) - Context API if needed for complex state
- **HTTP Client:** Fetch API or Axios for API communication
- **Build Tool:** Vite or Create React App

### 11.2 Page Layout & Structure

#### Single-Page Application Layout
```
┌─────────────────────────────────────────────────┐
│  Header: "Room Detection AI"                    │
│  (Simple, clean header with logo/title)        │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────────────────────┐  │
│  │  Upload Section                         │  │
│  │  - Drag & drop area                    │  │
│  │  - OR file input button                 │  │
│  │  - File name display                    │  │
│  │  - Process button (when file selected) │  │
│  └─────────────────────────────────────────┘  │
│                                                 │
│  ┌─────────────────────────────────────────┐  │
│  │  Blueprint Display Area                  │  │
│  │  (Full-width, scrollable)               │  │
│  │  - Image container                      │  │
│  │  - Canvas overlay with bounding boxes   │  │
│  │  - Loading indicator during processing  │  │
│  └─────────────────────────────────────────┘  │
│                                                 │
│  ┌─────────────────────────────────────────┐  │
│  │  Export Section                         │  │
│  │  (Visible after processing completes)   │  │
│  │  - Export Annotated Image button        │  │
│  │  - Export JSON button                   │  │
│  └─────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Design Philosophy:**
- **Single-page application:** All functionality on one page, no navigation
- **Progressive disclosure:** Export options appear only after processing completes
- **Focus on visualization:** Blueprint with bounding boxes is the primary output
- **Simple workflow:** Upload → Process → View → Export

### 11.3 Core UI Components

#### 11.3.1 File Upload Component
**Purpose:** Allow users to upload blueprint images (PNG/JPG)

**Features:**
- **Drag & Drop Zone:**
  - Large, clearly visible drop area (min 400x200px)
  - Visual feedback on drag-over (highlight border, background color change)
  - Text: "Drag blueprint image here (PNG or JPG)"
  - Accepts: PNG, JPG formats only
  - File size validation (max 50MB)
  
- **File Input Button (Alternative to drag & drop):**
  - "Browse Files" or "Select Blueprint" button
  - Opens standard file picker
  - Same file type restrictions (PNG, JPG)
  
- **File Preview:**
  - Display selected file name
  - File size display
  - File type indicator
  - Remove/clear button to reset selection
  
- **Process Button:**
  - Appears when valid file is selected
  - "Process Blueprint" label
  - Disabled during processing
  
- **Validation Feedback:**
  - Error messages for invalid file types (show accepted formats)
  - Error messages for files exceeding size limit
  - Success indicator when valid file selected

**States:**
- **Empty:** Show upload prompt with drag & drop zone
- **File Selected:** Show file name, size, and "Process" button
- **Invalid File:** Show error message, allow retry
- **Processing:** Disable upload, show loading state

#### 11.3.2 Blueprint Display Component
**Purpose:** Display the uploaded blueprint with detected room bounding boxes overlaid

**Features:**
- **Image Container:**
  - Full-width container (responsive to viewport)
  - Maintains image aspect ratio
  - Scrollable if image exceeds viewport height
  - Centered display
  - Background: Light gray (#f5f5f5) or white
  
- **Canvas Overlay:**
  - HTML5 Canvas positioned absolutely over image
  - Synchronized dimensions with image (matches image size exactly)
  - Renders bounding boxes dynamically based on API response
  - Redraws on window resize (maintains alignment)
  
- **Bounding Box Rendering:**
  - **Color:** Distinct colors per room (rotate through color palette)
  - **Style:** 2-3px solid outline
  - **Visibility:** All boxes visible by default
  - **Rendering:** React front-end renders automatically-created room boundaries on blueprint visualization
  
- **Loading Overlay:**
  - Semi-transparent overlay during processing
  - Loading spinner centered
  - Status text: "Processing blueprint..." or "Detecting rooms..."

**States:**
- **No Image:** Show placeholder text or empty state
- **Image Loaded (Before Processing):** Display image only, no bounding boxes
- **Processing:** Display image with loading overlay
- **Results:** Display image with bounding boxes overlay (canvas rendered)

#### 11.3.3 Status & Loading Component
**Purpose:** Provide feedback during processing

**Features:**
- **Loading Indicator:**
  - Spinner or progress animation
  - Status text: "Processing blueprint...", "Detecting rooms..."
  - Positioned as overlay on blueprint image or in upload section
  
- **Status Messages:**
  - "Uploading..." (during file upload to S3)
  - "Processing..." (during AI inference)
  - "Complete!" (when results ready)
  - Error messages (if processing fails)
  
- **Processing Time Display (Optional):**
  - Show elapsed time during processing
  - Display final processing time after completion

**States:**
- **Idle:** No indicator
- **Uploading:** Show upload progress/spinner
- **Processing:** Show spinner + status text overlay on image
- **Complete:** Show success message briefly, then hide
- **Error:** Show error message prominently

#### 11.3.4 Export Component
**Purpose:** Allow users to export the annotated blueprint image and JSON coordinates

**Features:**
- **Export Annotated Image Button:**
  - "Export Annotated Image" or "Download Image" button
  - Downloads PNG image with bounding boxes rendered
  - File name: `blueprint_annotated_[timestamp].png`
  - Image includes: Original blueprint + bounding boxes overlay
  
- **Export JSON Button:**
  - "Export JSON" or "Download Coordinates" button
  - Downloads JSON file with all room coordinates
  - File name: `blueprint_coordinates_[timestamp].json`
  - JSON format matches API response structure:
    ```json
    {
      "blueprint_id": "unique_identifier",
      "processing_time_ms": 15420,
      "detected_rooms": [
        {
          "id": "room_001",
          "bounding_box": [50, 50, 200, 300],
          "confidence": 0.95
        }
      ],
      "status": "success"
    }
    ```
  
- **Export Section Visibility:**
  - Hidden until processing completes successfully
  - Appears below blueprint display area
  - Both buttons visible side-by-side or stacked

**States:**
- **No Results:** Hidden
- **Results Available:** Visible with both export buttons enabled
- **Exporting:** Disable buttons during download, show brief feedback

#### 11.3.5 Error Display Component
**Purpose:** Show error messages clearly

**Features:**
- **Error Types:**
  - File upload errors (invalid format, size limit)
  - Processing errors (API failures, timeout)
  - Network errors (connection issues)
  
- **Error Display:**
  - Red or orange alert box
  - Clear error message
  - Actionable guidance ("Please try again", "Check file format")
  - Dismissible (X button)
  
- **Error Recovery:**
  - Retry button for transient errors
  - Clear error and return to upload state

### 11.4 User Flow & Interaction Patterns

#### Primary Flow: Upload → Process → View → Export

1. **Upload Phase:**
   - User lands on single-page application
   - Sees drag & drop upload area
   - User drags PNG/JPG file OR clicks "Browse Files"
   - File selected, file name displayed
   - "Process Blueprint" button appears
   - User clicks "Process"

2. **Processing Phase:**
   - Upload button disabled
   - File uploads to S3 (if needed)
   - Loading indicator appears (overlay on image area)
   - Status message: "Processing blueprint..."
   - Frontend polls status endpoint every 2-3 seconds
   - Blueprint image displayed (if available)

3. **Results Phase:**
   - Loading indicator disappears
   - Bounding boxes overlay rendered on blueprint via Canvas
   - Export section appears below blueprint
   - Two export buttons visible:
     - "Export Annotated Image" (downloads PNG with boxes)
     - "Export JSON" (downloads coordinates JSON)
   - User can export either or both files

4. **Reset Flow:**
   - User can upload a new file at any time
   - New upload clears previous results
   - Cycle repeats

#### Error Flow:
- Error occurs → Error message displayed prominently → User can retry upload or select new file

### 11.5 Visual Design Guidelines

#### Color Palette
- **Primary:** Blue (#2563eb) - for buttons, links
- **Success:** Green (#10b981) - for success states
- **Error:** Red (#ef4444) - for errors
- **Warning:** Orange (#f59e0b) - for warnings
- **Bounding Boxes:** 
  - Use distinct colors: Red, Blue, Green, Yellow, Purple, Cyan
  - Rotate through palette for multiple rooms
  - Ensure sufficient contrast against blueprint background

#### Typography
- **Headings:** Sans-serif (e.g., Inter, Roboto) - 24-32px
- **Body:** Sans-serif - 16px
- **Labels:** Sans-serif - 14px
- **Small Text:** Sans-serif - 12px

#### Spacing & Layout
- **Container Padding:** 24-32px
- **Component Spacing:** 16-24px between major sections
- **Button Padding:** 12px 24px
- **Border Radius:** 8px for cards, 4px for buttons

#### Responsive Design
- **Desktop (Primary):** Full-width layout, side-by-side panels
- **Tablet:** Stacked layout, maintain functionality
- **Mobile (Future):** Simplified layout, touch-friendly controls

### 11.6 Accessibility Considerations

- **Keyboard Navigation:**
  - All interactive elements keyboard accessible
  - Tab order logical
  - Enter/Space to activate buttons
  
- **Screen Reader Support:**
  - ARIA labels on buttons and inputs
  - Alt text for images
  - Status announcements for processing states
  
- **Visual Accessibility:**
  - Sufficient color contrast (WCAG AA minimum)
  - Focus indicators visible
  - Text resizable without breaking layout

### 11.7 UI States Summary

| State | Components Visible | User Actions Available |
|-------|-------------------|----------------------|
| **Initial** | Upload component (drag & drop) | Upload file (drag/drop or browse) |
| **File Selected** | Upload component + file preview + Process button | Process blueprint or change file |
| **Uploading** | Upload component + loading indicator | Wait (Process button disabled) |
| **Processing** | Blueprint image + loading overlay + status text | Wait (polling status) |
| **Success** | Blueprint with bounding boxes + Export section | Export annotated image, Export JSON, upload new file |
| **Error** | Error message + upload component | Retry upload or select new file |

### 11.8 Implementation Notes

- **Canvas Rendering:**
  - Use `useRef` for canvas element
  - Redraw bounding boxes when image loads or results update
  - Coordinate transformation: API returns 0-1000 range `[x_min, y_min, x_max, y_max]`, convert to pixel coordinates
  - Formula: `pixel_x = (normalized_x / 1000) * image_width`
  - Ensure canvas dimensions match image dimensions exactly
  
- **Image Export (Annotated Image):**
  - Create new canvas element (not displayed)
  - Draw original image onto canvas
  - Draw bounding boxes on top
  - Convert canvas to blob: `canvas.toBlob()`
  - Create download link and trigger download
  - File format: PNG
  
- **JSON Export:**
  - Use API response data directly
  - Convert to JSON string: `JSON.stringify(data, null, 2)`
  - Create blob: `new Blob([jsonString], { type: 'application/json' })`
  - Create download link and trigger download
  
- **Polling Implementation:**
  - Use `setInterval` or `setTimeout` for status polling
  - Poll every 2-3 seconds
  - Stop polling when status is "completed" or "failed"
  - Maximum polling duration: 60 seconds (timeout)
  - Clean up interval on component unmount
  
- **File Handling:**
  - Validate file type before upload (PNG/JPG only)
  - Show file preview if possible
  - Handle large files gracefully
  - Read file as data URL for preview: `FileReader.readAsDataURL()`
  
- **Performance:**
  - Lazy load image if large
  - Optimize canvas redraws (only redraw when needed)
  - Debounce resize events
  - Use `requestAnimationFrame` for smooth canvas updates

---

## 12. Out of Scope (for MVP)

- **Polygon detection** for irregular rooms (bounding boxes only)
- **User authentication/authorization** (simple API key sufficient)
- **Manual room boundary editing** in UI
- **Door and window detection**
- **Room name/type classification** (room name hints in API response)
- **Multi-floor blueprint separation**
- **Production-grade deployment** (no CI/CD, monitoring, etc.)
- **Mobile responsive design** (desktop-focused demo)
- **Batch processing** of multiple blueprints
- **Real-time collaboration** features
- **Data augmentation** during training (optional enhancement)
- **Confidence threshold filtering** (may be added later)

---

## 13. Future Enhancements (Post-MVP)

1. **Room Name Hints:** Extract and return room labels/names from blueprint text (e.g., "Bedroom", "Kitchen", "WC")
2. **Advanced Shape Detection:** Polygon boundaries for irregular rooms
3. **Semantic Segmentation:** Detect room types (bedroom, kitchen, bathroom)
4. **Feature Detection:** Doors, windows, stairs, fixtures
5. **User Editing Tools:** Manual adjustment of detected boundaries
6. **Multi-Floor Support:** Separate floor plan analysis
7. **Integration with Innergy's Existing Name Detection:** Combine boundary + name extraction
8. **Batch Processing:** Handle multiple blueprints simultaneously
9. **Data Augmentation:** Implement rotation, scaling, and other augmentations during training
10. **Confidence Threshold Filtering:** Filter detected rooms by confidence score
11. **Quantitative Metrics:** Add mAP, IoU, precision/recall metrics for model evaluation

---

## 14. Technical Constraints

### Must Use
- ✅ AWS as cloud platform
- ✅ AWS AI/ML services (Textract, SageMaker, Rekognition)
- ✅ React for frontend
- ✅ Processing time <30 seconds

### Cannot Use
- ❌ "Magic" or unproven approaches
- ❌ Non-AWS cloud platforms
- ❌ Third-party Document AI services (e.g., Google DocumentAI)

### Best Practices
- Follow established engineering principles
- Write clean, documented code
- Use serverless architecture for scalability
- Implement proper error handling
- Log everything for debugging

---

## 15. Questions & Assumptions

### Assumptions Made
- Blueprint images are reasonably clear and high-resolution
- Rooms are represented by enclosed wall boundaries
- Coordinate system origin is top-left (0,0)
- Most blueprints are residential with 3-15 rooms
- Simple bounding boxes are acceptable for irregular spaces
- Demo can use simplified test blueprints

### Open Questions for Future Clarification
- What is the typical resolution/size of Innergy blueprints?
- Are there specific architectural standards to follow?
- Should the system handle scanned vs. digital-native blueprints differently?
- What level of accuracy is "production-ready" for Innergy?

---

## 16. Success Metrics (Demo Evaluation)

### Technical Excellence
- [ ] Code quality and organization
- [ ] Proper use of AWS services (SageMaker, Lambda, API Gateway, S3)
- [ ] Clean architecture and separation of concerns
- [ ] Error handling and edge case management
- [ ] Successful YOLOv8 model training and deployment

### Functional Completeness
- [ ] Successfully detects rooms in test blueprints (qualitative assessment)
- [ ] Meets <30 second processing requirement
- [ ] Visually accurate bounding box coordinates (qualitative assessment)
- [ ] Working end-to-end flow (upload → process → visualize)
- [ ] Async processing with polling works correctly

### Presentation Quality
- [ ] Clear, compelling demo video/presentation
- [ ] Professional documentation
- [ ] Well-articulated technical decisions
- [ ] Demonstrates business value

### Innovation & Polish
- [ ] Creative problem-solving approach (using pre-annotated COCO format instead of SVG parsing)
- [ ] Polished user interface
- [ ] Thoughtful architecture decisions
- [ ] Shows potential for real-world application

**Note:** Success metrics are primarily qualitative for MVP. Quantitative metrics (mAP, IoU, precision/recall) may be added later as the model is refined.

---

## Appendix A: Helpful Resources

### AWS Documentation
- [Amazon SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [SageMaker Serverless Inference](https://docs.aws.amazon.com/sagemaker/latest/dg/serverless-endpoints.html)
- [SageMaker Custom Containers](https://docs.aws.amazon.com/sagemaker/latest/dg/docker-containers.html)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [API Gateway REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html)

### YOLOv8 Resources
- [Ultralytics YOLOv8 Documentation](https://docs.ultralytics.com/)
- [YOLOv8 GitHub Repository](https://github.com/ultralytics/ultralytics)
- [YOLOv8 Training Guide](https://docs.ultralytics.com/modes/train/)

### Computer Vision & ML Resources
- OpenCV for image preprocessing
- PyTorch (YOLOv8 backend)
- YOLO format specification for object detection

---

**Document Version:** 2.0  
**Last Updated:** [Current Date]  
**Author:** Gauntlet Project Team  
**Target Audience:** Development team, Innergy stakeholders

**Version History:**
- **v2.0:** Updated with YOLOv8 fine-tuning approach, auto-labeling strategy, async API design, and clarified technical specifications
- **v1.0:** Initial PRD draft