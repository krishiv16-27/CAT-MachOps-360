# API Contracts — CAT MachOps 360

All endpoints prefixed with `/api/v1`.
All responses wrapped: `{ "data": ..., "meta": { "timestamp": "ISO8601", "total": int? } }`
All errors: `{ "error": { "code": "SNAKE_CASE", "message": "human readable" } }`
Auth: `Authorization: Bearer <jwt_token>`

---

## Auth

### POST /auth/login
**Body:** `{ "email": str, "password": str }`
**Response:**
```json
{
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "user_id": "uuid",
      "email": "str",
      "name": "str",
      "role": "operator|supervisor|engineer|safety_officer|maintenance_engineer|admin",
      "operator_id": "uuid|null"
    }
  }
}
```

### POST /auth/refresh
**Body:** `{ "refresh_token": str }`
**Response:** Same as login

### GET /auth/me
**Response:** `{ "data": { ...user object } }`

---

## Operators

### GET /operators
**Query:** `?page=1&page_size=50&site_id=&status=active|inactive`
**Roles:** supervisor, engineer, safety_officer, admin
**Response:**
```json
{
  "data": [{
    "operator_id": "uuid",
    "name": "str",
    "employee_code": "str",
    "experience_years": 5,
    "skill_level": 3,
    "certification": "CAT-EXC-L2",
    "certification_expiry": "2025-06-01",
    "current_machine_id": "uuid|null",
    "current_task_id": "uuid|null",
    "shift_status": "ON_SHIFT|OFF_SHIFT|ON_BREAK",
    "safety_score": 87.5,
    "wearable_connected": true,
    "active_alerts_count": 1,
    "authorization_status": "AUTHORIZED|BLOCKED|REVIEW|PENDING"
  }],
  "meta": { "total": 10, "page": 1, "page_size": 50 }
}
```

### GET /operators/:id
**Response:** Full operator object + today's shift summary

### GET /operators/:id/timeline
**Query:** `?date=2024-01-15`
**Response:** Ordered list of task periods, break periods, safety events for the day

### GET /operators/:id/safety-score
**Response:**
```json
{
  "data": {
    "overall": 87.5,
    "label": "Operational Safety Score (Demo Index)",
    "components": {
      "seatbelt_compliance": { "score": 95.0, "weight": 0.25, "events_count": 1 },
      "proximity_events":    { "score": 80.0, "weight": 0.20, "events_count": 3 },
      "speed_violations":    { "score": 100.0,"weight": 0.15, "events_count": 0 },
      "incident_rate":       { "score": 90.0, "weight": 0.20, "incidents_count": 1 },
      "prestart_compliance": { "score": 100.0,"weight": 0.10 },
      "training_completion": { "score": 75.0, "weight": 0.10, "pending_modules": 2 }
    }
  }
}
```

### GET /operators/:id/training-recommendations
**Response:** `{ "data": [{ "module_id", "title", "reason", "priority", "due_date" }] }`

---

## Machines

### GET /machines
**Query:** `?status=active|inactive&site_id=&type=`
**Response:** List of machine summaries

### GET /machines/:id
**Response:** Full machine detail

### GET /machines/:id/health
**Response:**
```json
{
  "data": {
    "machine_id": "uuid",
    "overall_health": 92.0,
    "components": {
      "engine":      { "score": 95.0, "rpm": 1450, "temperature_c": 88, "oil_pressure_psi": 55, "hours": 4821 },
      "fuel":        { "score": 78.0, "level_pct": 67, "consumption_rate_lph": 12.4, "efficiency_score": 82 },
      "hydraulics":  { "score": 91.0, "pressure_bar": 220, "temperature_c": 55, "flow_lpm": 180 },
      "electrical":  { "score": 99.0, "battery_voltage": 13.8 },
      "mechanical":  { "score": 94.0, "vibration_g": 0.3, "brake_status": "OK", "track_condition": "GOOD" },
      "maintenance": { "score": 88.0, "last_service_days_ago": 12, "next_service_due_hours": 180, "status": "OK" }
    },
    "active_faults": [],
    "maintenance_risk": "LOW"
  }
}
```

### GET /machines/:id/telemetry
**Query:** `?from_ts=&to_ts=&interval=1min`
**Response:** Time-series telemetry records

---

## Tasks

### GET /tasks
**Query:** `?operator_id=&machine_id=&status=&date=`
**Response:** Task list

### GET /tasks/:id
**Response:** Full task with progress + ETA

### POST /tasks/:id/start
### POST /tasks/:id/complete
### PATCH /tasks/:id — update progress

---

## Alerts

### GET /alerts
**Query:** `?severity=&resolved=false&machine_id=&operator_id=&from_ts=&page=1`
**Response:** Alert list

### GET /alerts/:id
### POST /alerts/:id/acknowledge
**Body:** `{ "note": str? }`

---

## Incidents

### GET /incidents
### GET /incidents/:id
### POST /incidents
**Body:** `{ "machine_id", "operator_id", "task_id"?, "category", "severity", "description", "trigger_data"? }`
### PATCH /incidents/:id

---

## Pre-Start

### GET /prestart/checklist
**Query:** `?machine_id=&operator_id=`
**Response:** Checklist items with current pass/fail status

### POST /prestart/submit
**Body:** `{ "machine_id", "operator_id", "items": [{ "item_id", "passed": bool, "note"? }] }`
**Response:** `{ "authorization_status": "AUTHORIZED|BLOCKED|REVIEW", "blocked_reasons": [], "review_reasons": [] }`

---

## ML

### POST /ml/predict-eta
**Body:**
```json
{
  "task_type": "EXCAVATION",
  "machine_type": "EXCAVATOR",
  "machine_age_years": 3,
  "operator_skill_level": 3,
  "operator_experience_years": 5,
  "target_quantity": 500,
  "material_type": "CLAY",
  "weather_condition": "CLOUDY",
  "temperature_celsius": 22,
  "rainfall_mm": 0,
  "wind_speed_kmh": 15,
  "terrain_type": "FLAT",
  "machine_load_percent": 70
}
```
**Response:** `{ "data": { "predicted_minutes": 72, "confidence_interval": [62, 82], "mock": false } }`

### POST /ml/anomaly-check
**Body:** `{ "operator_id": "uuid", "window_minutes": 30 }`
**Response:** `{ "data": { "score": -0.12, "label": "UNUSUAL", "reason": "...", "contributing_features": {} } }`

---

## Simulator

### POST /simulator/activate
**Body:** `{ "scenario": "PROXIMITY_HAZARD", "machine_id"?: "uuid", "operator_id"?: "uuid" }`

### POST /simulator/reset
### GET /simulator/status

---

## CV

### POST /cv/events (internal)
### GET /cv/events
### POST /cv/simulate
**Body:** `{ "event_type": "person_detected", "machine_id": "uuid", "distance_m": 3.5 }`

---

## Analytics

### GET /analytics/productivity
**Query:** `?site_id=&from_ts=&to_ts=`

### GET /analytics/site-overview
**Response:** The 7 KPI card values

---

## Copilot

### POST /copilot/query
**Body:** `{ "question": str, "context_filter"?: { "machine_id"?: str } }`
**Response:** `{ "data": { "answer": str, "sources": [...], "structured_data"?: {} } }`

### GET /copilot/history
### DELETE /copilot/history

---

## WebSocket

`ws://localhost:8000/ws?token=<jwt>`

See `docs/event-schemas.md` for message formats.
