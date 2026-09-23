# Spec 7 — Dashcam & Computer Vision

## Status: READY FOR IMPLEMENTATION

---

## Requirements

### REQ-7.1 CV architecture
The system must support real CV input but not depend on it for the demo.
Architecture: **pluggable adapter pattern**.
```
CVAdapter (abstract)
  ├── SimulatedCVAdapter    ← MVP, always works, no GPU
  ├── OpenCVAdapter         ← optional, local video file
  └── YOLOAdapter           ← future/optional
```

### REQ-7.2 Simulated CV adapter (P0 — must work)
`cv/simulator/simulated_cv_adapter.py` produces realistic CV events without a camera:
- Generates events at configurable intervals
- Event types: person_detected, vehicle_detected, obstacle_detected, restricted_zone_entry
- Each event has: timestamp, camera_id, machine_id, estimated_distance, confidence, zone
- Optional attention events: eye_closure_event, yawn_event (labelled as demo only)
- Injected into the safety engine pipeline identically to real CV events

### REQ-7.3 Dashcam events table
```
dashcam_event_id, timestamp, camera_id, machine_id, operator_id,
person_detected (bool), vehicle_detected (bool), obstacle_detected (bool),
restricted_zone_entry (bool), estimated_distance_m (float),
attention_event (bool), eye_closure_event (bool), yawn_event (bool),
confidence (0-1), event_type (str), frame_path (nullable str),
raw_metadata (JSON)
```

### REQ-7.4 CV → Safety Engine integration
```
CVEvent (from any adapter)
  → POST /cv/events  (internal endpoint)
  → safety_engine.evaluate_cv_event(event)
  → if person_detected AND distance < threshold → proximity alert
  → if restricted_zone_entry → zone violation alert
  → alert published to Redis → WebSocket → dashboard + watch
```

### REQ-7.5 Dashcam page (`/dashcam`)
- Simulated camera feed: animated placeholder showing current CV events
- Recent events list: type, machine, distance, timestamp, confidence
- Event statistics: detections today by type
- "Simulate Event" button (triggers a specific CV event for demo)
- Camera status panel: which cameras are active (simulated)

### REQ-7.6 Demo scenario: dashcam person detection
When scenario `dashcam_person_detection` is activated:
1. Simulated CV event: person_detected, distance=3.8m, zone=EXC001_OPERATING_ZONE
2. Safety engine creates CRITICAL proximity alert
3. Dashboard receives alert
4. Watch navigates to alert screen + vibrate
5. Incident draft created
6. CV event recorded in dashcam_events

---

## Design

### Adapter interface
```python
# cv/adapters/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class CVEvent:
    timestamp: str
    camera_id: str
    machine_id: str
    operator_id: str | None
    person_detected: bool
    vehicle_detected: bool
    obstacle_detected: bool
    restricted_zone_entry: bool
    estimated_distance_m: float | None
    confidence: float
    event_type: str
    attention_event: bool = False
    raw_metadata: dict = None

class CVAdapter(ABC):
    @abstractmethod
    async def get_events(self) -> list[CVEvent]:
        ...

    @abstractmethod
    async def start(self):
        ...

    @abstractmethod
    async def stop(self):
        ...
```

### Simulated adapter
```python
# cv/simulator/simulated_cv_adapter.py
class SimulatedCVAdapter(CVAdapter):
    # Generates events from pre-defined scenario scripts
    # or random within realistic distributions
    # Configurable: event_rate, scenario, seed
```

### CV API
```
POST /cv/events          internal — receive CV event from adapter
GET  /cv/events          paginated CV event history
GET  /cv/cameras         camera status list
POST /cv/simulate        demo trigger: inject a specific CV event type
```

### Frontend dashcam page layout
```
┌─────────────────────────────────────────────────────┐
│ DASHCAM MONITORING                                  │
├────────────────────┬────────────────────────────────┤
│ CAMERA FEEDS       │  RECENT EVENTS                 │
│ [CAM-EXC001-FRONT] │  ─────────────────────────     │
│  ● LIVE (sim)      │  Person Detected  3.8m CRIT    │
│                    │  Vehicle Near     12m  MED      │
│ [CAM-EXC002-FRONT] │  Zone Entry       -    HIGH    │
│  ● LIVE (sim)      │                                │
├────────────────────┴────────────────────────────────┤
│ STATISTICS: Persons Today: 4 | Vehicles: 7 | ...   │
│ [SIMULATE PERSON DETECTION]  [SIMULATE ZONE ENTRY] │
└─────────────────────────────────────────────────────┘
```

---

## Tasks

- [ ] Create cv/adapters/base.py (CVEvent dataclass + CVAdapter ABC)
- [ ] Create cv/simulator/simulated_cv_adapter.py
- [ ] Create cv/adapters/opencv_adapter.py (stub, not required for demo)
- [ ] Create backend/app/routers/cv.py
- [ ] Create backend/app/services/cv_service.py (adapter wiring)
- [ ] Create DashcamEvent SQLAlchemy model + Pydantic schemas
- [ ] Wire CV events → safety engine
- [ ] Create frontend dashcam page (/dashcam)
- [ ] Create simulated camera feed component
- [ ] Create CV events list component
- [ ] Create "Simulate Event" demo button
- [ ] Test full flow: simulate → alert → watch
