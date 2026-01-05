# 🎥 CCTV Analytics System

A production-ready, scalable computer vision system for real-time analytics and event detection. Built with clean architecture principles, supporting multiple detection models (person counting, fire detection, mask detection, queue detection) with easy extensibility.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Adding New Detectors](#adding-new-detectors)
- [Webhook Integration](#webhook-integration)
- [Production Deployment](#production-deployment)
- [API Reference](#api-reference)

## 🎯 Overview

This system processes video streams from multiple cameras, runs various AI detection models in parallel, and sends real-time events to your Rails backend via webhooks. It's designed to be:

- **Modular**: Easy to add new detection types
- **Scalable**: Handles multiple cameras efficiently
- **Production-Ready**: Proper logging, error handling, and configuration management
- **Extensible**: Plugin-based detector architecture

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Rails Backend API                            │
│                    (Receives Webhook Events)                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ HTTP Webhooks
                                │ (person_in, person_out, fire_detected, etc.)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CCTV Analytics System                             │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Main Entry Point (main.py)                  │  │
│  │              Replaces shell scripts, unified CLI                │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                                │                                      │
│                                ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Camera Manager                                │  │
│  │         (Loads cameras from database, manages processes)        │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                                │                                      │
│                    ┌───────────┼───────────┐                        │
│                    ▼           ▼           ▼                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │
│  │  Camera 1    │ │  Camera 2    │ │  Camera N    │               │
│  │  Process     │ │  Process      │ │  Process      │               │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘               │
│         │                 │                 │                        │
│         └─────────┬───────┴─────────┬──────┘                        │
│                   ▼                 ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Camera Pipeline (per camera)                      │  │
│  │                                                                │  │
│  │  ┌────────────────────────────────────────────────────────┐   │  │
│  │  │         Detector Factory                                │   │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │  │
│  │  │  │ Person   │ │ Fire     │ │ Mask     │ │ Queue    │    │   │  │
│  │  │  │ Detector │ │ Detector │ │ Detector │ │ Detector │    │   │  │
│  │  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │   │  │
│  │  └───────┼─────────────┼─────────────┼────────────┼─────────┘   │  │
│  │          │             │             │             │              │  │
│  │          └─────────────┴─────────────┴─────────────┘              │  │
│  │                      ▼                                              │  │
│  │          ┌───────────────────────┐                                 │  │
│  │          │   Event Aggregator    │                                 │  │
│  │          │  (Combines detections)│                                 │  │
│  │          └───────────┬───────────┘                                 │  │
│  │                      │                                              │  │
│  │          ┌───────────┴───────────┐                                 │  │
│  │          ▼                         ▼                                │  │
│  │  ┌──────────────┐         ┌──────────────┐                         │  │
│  │  │   Tracker    │         │  Webhook     │                         │  │
│  │  │  (StrongSORT)│         │   Service    │                         │  │
│  │  └──────────────┘         └──────┬───────┘                         │  │
│  │                                   │                                  │  │
│  └───────────────────────────────────┼──────────────────────────────────┘  │
│                                        │                                      │
└────────────────────────────────────────┼──────────────────────────────────────┘
                                         │
                                         ▼
                            ┌──────────────────────┐
                            │   PostgreSQL DB      │
                            │  (Events, Attendance) │
                            └──────────────────────┘
```

### Folder Structure

```
cctv/
├── main.py                      # Main entry point (replaces shell scripts)
├── config/
│   ├── config.yaml             # Main configuration
│   └── config.example.yaml     # Example configuration
├── src/
│   └── cctv/
│       ├── core/               # Core interfaces and base classes
│       │   ├── base_detector.py      # BaseDetector abstract class
│       │   ├── detector_factory.py   # Detector factory pattern
│       │   └── ...
│       ├── detectors/          # Detection modules (plugins)
│       │   ├── person_detector.py   # Person detection & counting
│       │   ├── fire_detector.py     # Fire detection
│       │   ├── mask_detector.py     # Mask detection (to be added)
│       │   └── queue_detector.py   # Queue detection (to be added)
│       ├── services/           # Service layer
│       │   └── webhook_service.py  # Webhook delivery to Rails
│       ├── pipeline/           # Processing pipeline
│       │   └── camera_pipeline.py  # Camera processing orchestration
│       ├── config/             # Configuration management
│       │   └── config_manager.py   # Centralized config loading
│       ├── database/           # Database layer
│       ├── managers/           # Resource managers
│       └── utils/              # Utilities
├── scripts/                    # Utility scripts (migration, setup, etc.)
├── tests/                      # Test suite
└── README.md                   # This file
```

## ✨ Features

### Core Capabilities

- **Multi-Detector Support**: Run multiple detection models simultaneously
  - Person counting (IN/OUT tracking)
  - Fire detection
  - Mask detection (ready for implementation)
  - Queue/crowd detection (ready for implementation)
  
- **Plugin Architecture**: Easy to add new detection types without modifying core code

- **Webhook Integration**: Real-time event delivery to Rails backend
  - Configurable endpoints per event type
  - Retry logic and error handling
  - Async delivery queue

- **Production-Ready**:
  - Unified entry point (no shell scripts)
  - Centralized configuration management
  - Comprehensive logging
  - Health checks
  - Graceful shutdown

- **Scalable**:
  - Multi-camera support (each in separate process)
  - GPU acceleration support
  - Efficient resource management

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- (Optional) NVIDIA GPU with CUDA support
- RTSP cameras or video files

### Installation

1. **Clone and setup environment**:
```bash
cd cctv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
pip install -r requirements_face.txt
```

2. **Setup database**:
```bash
# Create database and enable pgvector
createdb face_recognition
psql face_recognition -c "CREATE EXTENSION vector;"

# Run migrations
python scripts/setup/setup_database.py
```

3. **Configure environment**:
```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit config.yaml with your settings
# Or set environment variables:
export POSTGRES_HOST=localhost
export POSTGRES_PASSWORD=your_password
export WEBHOOK_BASE_URL=http://your-rails-api.com
```

4. **Add cameras**:
```bash
# Add camera via CLI
python scripts/cli/manage_cameras.py add \
  --camera-id entrance \
  --rtsp-url "rtsp://admin:password@192.168.1.101:554/stream1" \
  --location "Main Entrance" \
  --organization-id 1
```

5. **Run the system**:
```bash
# Run all cameras
python main.py run

# Run specific camera
python main.py run --camera-id entrance

# Run cameras for organization
python main.py run --org-id 1

# Start API server
python main.py api

# List cameras
python main.py list-cameras

# Health check
python main.py health
```

## ⚙️ Configuration

### Configuration File

Main configuration is in `config/config.yaml`. See `config/config.example.yaml` for all options.

### Environment Variables

Override configuration with environment variables:

```bash
# Database
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=face_recognition
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password

# Webhooks
export WEBHOOK_BASE_URL=http://your-rails-api.com

# Note: RTSP URLs are now stored directly in the database
# No need for environment variables - add cameras via CLI or API
```

### Detector Configuration

Enable/disable detectors in `config.yaml`:

```yaml
detectors:
  enabled:
    - person
    - fire
    # - mask
    # - queue
```

### Webhook Configuration

Configure webhook endpoints for Rails integration:

```yaml
webhooks:
  enabled: true
  base_url: http://localhost:3000
  timeout: 5
  retry_attempts: 3
  
  endpoints:
    person_in: /api/v1/events/person_in
    person_out: /api/v1/events/person_out
    fire_detected: /api/v1/events/fire_detected
```

## 🔌 Adding New Detectors

The system uses a plugin-based architecture. To add a new detector:

### Step 1: Create Detector Class

Create a new file in `src/cctv/detectors/` (e.g., `mask_detector.py`):

```python
from cctv.core.base_detector import BaseDetector, DetectionResult
import numpy as np
from typing import Dict, Any, Optional
import logging

class MaskDetector(BaseDetector):
    """Mask detection detector"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self.model = None
    
    def initialize(self) -> bool:
        """Initialize mask detection model"""
        # Load your model here
        # self.model = load_mask_model()
        self._initialized = True
        return True
    
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """Detect masks in frame"""
        # Run detection
        detections = []
        # ... your detection logic ...
        
        return DetectionResult(
            detector_type='mask',
            detections=detections
        )
    
    def get_detector_type(self) -> str:
        return 'mask'
    
    def cleanup(self):
        # Cleanup resources
        self._initialized = False
```

### Step 2: Register Detector

Add to `src/cctv/detectors/__init__.py`:

```python
from cctv.detectors.mask_detector import MaskDetector

__all__ = ['PersonDetector', 'FireDetector', 'MaskDetector']
```

The detector is automatically registered via the factory pattern.

### Step 3: Add Configuration

Add detector config to `config.yaml`:

```yaml
mask_detection:
  model: mask_model.pt
  confidence: 0.5
  device: cuda
```

### Step 4: Enable Detector

Enable in `config.yaml`:

```yaml
detectors:
  enabled:
    - person
    - mask  # Add here
```

### Step 5: Add Webhook Endpoint (Optional)

If you want webhook events:

```yaml
webhooks:
  endpoints:
    mask_detected: /api/v1/events/mask_detected
```

That's it! The detector will automatically be loaded and run for all cameras.

## 🔗 Webhook Integration

### Event Format

Events are sent as HTTP POST requests to your Rails API:

```json
{
  "event_type": "person_in",
  "timestamp": "2024-01-15T10:30:00.123456",
  "camera_id": "entrance",
  "organization_id": 1,
  "data": {
    "track_id": 42,
    "confidence": 0.95,
    "bbox": [100, 200, 300, 400],
    "position": {"x": 200, "y": 300}
  }
}
```

### Rails Controller Example

```ruby
# app/controllers/api/v1/events_controller.rb
class Api::V1::EventsController < ApplicationController
  skip_before_action :verify_authenticity_token
  
  def person_in
    event = Event.create!(
      event_type: 'person_in',
      camera_id: params[:camera_id],
      organization_id: params[:organization_id],
      data: params[:data],
      timestamp: params[:timestamp]
    )
    
    # Process event (e.g., update attendance)
    AttendanceService.new.handle_person_in(event)
    
    render json: { status: 'ok' }, status: :created
  end
  
  def fire_detected
    # Handle fire detection event
    AlertService.new.send_fire_alert(params)
    render json: { status: 'ok' }, status: :created
  end
end
```

### Supported Event Types

- `person_in` - Person entered zone
- `person_out` - Person exited zone
- `fire_detected` - Fire detected in frame
- `mask_detected` - Mask detection (when implemented)
- `queue_detected` - Queue/crowd detected (when implemented)

### Webhook Reliability

- **Async Delivery**: Webhooks are sent asynchronously via queue
- **Retry Logic**: Failed webhooks are retried up to 3 times
- **Error Handling**: Errors are logged but don't block processing
- **Queue Monitoring**: Check queue size via `webhook_service.get_queue_size()`

## 🚢 Production Deployment

### Systemd Service

Create `/etc/systemd/system/cctv.service`:

```ini
[Unit]
Description=CCTV Analytics System
After=network.target postgresql.service

[Service]
Type=simple
User=cctv
WorkingDirectory=/opt/cctv
Environment="PATH=/opt/cctv/venv/bin"
ExecStart=/opt/cctv/venv/bin/python main.py run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable cctv
sudo systemctl start cctv
sudo systemctl status cctv
```

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements_face.txt

COPY . .
CMD ["python", "main.py", "run"]
```

### Monitoring

- **Logs**: Check `logs/app.log`
- **Health**: `python main.py health`
- **Metrics**: Monitor GPU usage, queue sizes, event rates

### Scaling

- **Horizontal**: Run multiple instances, each handling different cameras
- **Vertical**: Increase GPU memory, CPU cores
- **Database**: Use connection pooling, read replicas

## 📚 API Reference

### Main Entry Point

```bash
python main.py <command> [options]

Commands:
  run              Run camera processing system
  api              Start REST API server
  list-cameras     List available cameras
  health           System health check
```

### Detector Interface

All detectors must implement `BaseDetector`:

```python
class BaseDetector(ABC):
    def initialize(self) -> bool
    def detect(self, frame: np.ndarray) -> DetectionResult
    def get_detector_type(self) -> str
    def cleanup(self)
```

### Webhook Service

```python
webhook_service = WebhookService(config, logger)
webhook_service.send_event(
    event_type='person_in',
    data={'track_id': 42},
    camera_id='entrance',
    organization_id=1
)
```

## 🤝 Contributing

1. Follow the detector interface pattern
2. Add tests for new detectors
3. Update documentation
4. Ensure GPU compatibility

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- InsightFace for face recognition
- StrongSORT for tracking
- PostgreSQL + pgvector

---

**Need Help?** Check the [SETUP.md](SETUP.md) for detailed setup instructions.
