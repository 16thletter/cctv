# Architecture Documentation

## Design Principles

### 1. Clean Architecture

The system follows clean architecture principles with clear separation of concerns:

- **Core Layer**: Base interfaces and abstractions
- **Detectors Layer**: Plugin-based detection implementations
- **Services Layer**: Business logic (webhooks, etc.)
- **Pipeline Layer**: Orchestration and coordination
- **Infrastructure Layer**: Database, file I/O, external APIs

### 2. Plugin Architecture

Detectors are implemented as plugins that:
- Implement the `BaseDetector` interface
- Are automatically discovered and loaded
- Can be enabled/disabled via configuration
- Don't require core code changes

### 3. Event-Driven Design

The system emits events for all significant occurrences:
- Detection events (person_in, fire_detected, etc.)
- Events are sent via webhooks to Rails backend
- Events are also logged to database

## Component Details

### BaseDetector Interface

All detectors must inherit from `BaseDetector`:

```python
class BaseDetector(ABC):
    def initialize(self) -> bool
    def detect(self, frame: np.ndarray) -> DetectionResult
    def get_detector_type(self) -> str
    def cleanup(self)
```

### DetectorFactory

The factory pattern is used to create detector instances:

- Automatically discovers available detectors
- Creates instances based on configuration
- Handles initialization errors gracefully

### CameraPipeline

Orchestrates the entire processing flow:

1. Frame capture
2. Run all enabled detectors
3. Update tracker (if person detector active)
4. Generate events
5. Send webhooks
6. Log to database

### WebhookService

Handles async webhook delivery:

- Queue-based async delivery
- Retry logic with exponential backoff
- Configurable endpoints per event type
- Error handling and logging

## Data Flow

```
Camera Stream
    ↓
CameraPipeline.process_frame()
    ↓
DetectorFactory.create_detectors()
    ↓
[PersonDetector, FireDetector, ...].detect()
    ↓
DetectionResult objects
    ↓
Event Aggregation
    ↓
WebhookService.send_event()
    ↓
Rails API (HTTP POST)
```

## Extension Points

### Adding a New Detector

1. Create detector class inheriting `BaseDetector`
2. Implement required methods
3. Add to `detectors/__init__.py`
4. Add configuration section
5. Enable in `detectors.enabled` list

### Adding a New Event Type

1. Emit event in detector or pipeline
2. Add webhook endpoint mapping
3. Handle in Rails controller

### Adding a New Service

1. Create service class
2. Initialize in pipeline
3. Use as needed

## Performance Considerations

- **GPU Acceleration**: All detectors support CUDA
- **Frame Skipping**: Configurable skip_frames for performance
- **Async Webhooks**: Non-blocking event delivery
- **Process Isolation**: Each camera in separate process
- **Resource Pooling**: Reuse models across frames

## Security

- RTSP URLs in `.env` (not in database)
- Database credentials via environment variables
- Webhook authentication (can be added)
- Input validation on all configs


