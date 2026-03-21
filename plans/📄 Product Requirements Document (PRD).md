# 📄 Product Requirements Document (PRD)

## 1. Project Overview

**System Name:**
 Road Damage Detection System

**Objective:**
 A web-based platform that allows users to upload images or stream video for detecting road defects using a YOLO-based model, and visualize results in real time.

------

## 2. Core Features

### 2.1 User Authentication

- User registration (email + password)
- Login / logout
- JWT-based authentication
- Optional: role (admin/user)

------

### 2.2 Image Inference

- Upload single image
- Run YOLO inference
- Return:
    - Annotated image
    - Detection results:
        - label (crack, pothole, etc.)
        - confidence
        - bounding box

------

### 2.3 Video / Real-time Inference (WebSocket)

- Stream frames from:
    - webcam OR uploaded video
- Backend processes frames in real-time
- Return annotated frames via WebSocket
- Display live detection overlay in frontend

------

### 2.4 History & Database

- Store:
    - uploaded images
    - inference results
    - timestamps
    - user ID
- Allow users to:
    - view history
    - re-open results

------

### 2.5 Frontend UI

- Login/Register pages
- Dashboard
- Image upload interface
- Real-time video inference page
- History page



### 2.6 Model Selection (NEW FEATURE)

#### Objective

Allow users to select different YOLO models when performing inference, enabling flexibility in:

- accuracy vs speed trade-offs
- different trained datasets (e.g., crack-only vs multi-defect)

------

### Functional Requirements

#### Model Selection (Image Inference)

- User can select a model before uploading image
- Selected model is used for inference
- Default model is pre-selected

------

#### Model Selection (Real-time Video)

- User selects model before starting stream
- Model remains fixed during session
- Optional: allow switching model (restart stream required)

------

#### Supported Models (Initial Set)

Example:

```
yolov8n (fast, low accuracy)
yolov8s (balanced)
yolov8m (higher accuracy)
custom-road-v1 (your trained model)
```

------

#### Backend Requirements

- Maintain a **model registry**
- Load models dynamically or cache them in memory
- Validate model name before inference

------

#### Frontend Requirements

- Dropdown / selector:
    - placed near upload button or video controls
- Display current selected model

------

#### Persistence

- Store selected model in inference history

------







## 3. Non-Functional Requirements

### Performance

- Image inference < 2 seconds
- Video latency < 500ms/frame (target)

### Scalability

- Modular backend (Flask blueprint structure)
- Separate inference module

### Security

- Password hashing (bcrypt)
- JWT authentication
- Input validation