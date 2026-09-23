# WebSocket Event Schemas — CAT MachOps 360

## Connection
```
ws://localhost:8000/ws?token=<jwt_access_token>
```

All messages are JSON. All timestamps are ISO 8601 UTC.

---

## Server → Client Events

### ALERT
Fired when safety engine creates a new alert.
```json
{
  "type": "ALERT",
  "payload": {
    "alert_id": "uuid",
    "timestamp": "2024-01-15T08:42:00Z",
    "site_id": "uuid",
    "zone_id": "uuid",
    "machine_id": "uuid",
    "operator_id": "uuid",
    "task_id": "uuid|null",
    "alert_type": "PROXIMITY_CRITICAL|SEATBELT_UNFASTENED|SPEED_VIOLATION|...",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "trigger_data": {},
    "message": "Person detected at 3.5m — critical proximity threshold exceeded",
    "recommended_action": "Stop machine immediately. Check surroundings.",
    "acknowledged": false
  }
}
```

### ALERT_ACKNOWLEDGED
```json
{
  "type": "ALERT_ACKNOWLEDGED",
  "payload": {
    "alert_id": "uuid",
    "acknowledged_by": "uuid",
    "acknowledged_at": "2024-01-15T08:42:30Z"
  }
}
```

### TELEMETRY_UPDATE
Fired every 5 seconds per active machine (summary only, not full row).
```json
{
  "type": "TELEMETRY_UPDATE",
  "payload": {
    "machine_id": "uuid",
    "timestamp": "2024-01-15T08:42:00Z",
    "engine_rpm": 1450,
    "engine_temperature_c": 88,
    "fuel_level_pct": 67,
    "machine_load_pct": 72,
    "machine_speed_kmh": 4.2,
    "hydraulic_pressure_bar": 218,
    "idle_time_min": 3,
    "operator_id": "uuid"
  }
}
```

### TASK_UPDATE
```json
{
  "type": "TASK_UPDATE",
  "payload": {
    "task_id": "uuid",
    "operator_id": "uuid",
    "machine_id": "uuid",
    "status": "IN_PROGRESS|COMPLETED|DELAYED|PAUSED",
    "progress_pct": 68,
    "eta_minutes": 18,
    "completed_quantity": 340,
    "target_quantity": 500
  }
}
```

### OPERATOR_UPDATE
```json
{
  "type": "OPERATOR_UPDATE",
  "payload": {
    "operator_id": "uuid",
    "continuous_operating_minutes": 47,
    "fatigue_risk_indicator": 0.22,
    "attention_risk_indicator": 0.18,
    "heart_rate": 78,
    "wearable_connected": true,
    "safety_score": 87.5,
    "active_alerts_count": 1
  }
}
```

### INCIDENT_CREATED
```json
{
  "type": "INCIDENT_CREATED",
  "payload": {
    "incident_id": "uuid",
    "timestamp": "2024-01-15T08:42:05Z",
    "machine_id": "uuid",
    "operator_id": "uuid",
    "severity": "HIGH",
    "category": "PROXIMITY",
    "description": "Auto-created from CRITICAL proximity alert"
  }
}
```

### SCENARIO_ACTIVATED
```json
{
  "type": "SCENARIO_ACTIVATED",
  "payload": {
    "scenario": "PROXIMITY_HAZARD",
    "description": "Simulating person detected at 3.5m from EXC001",
    "machine_id": "uuid",
    "operator_id": "uuid",
    "activated_at": "2024-01-15T08:42:00Z"
  }
}
```

### KPI_UPDATE
Fired every 30 seconds with updated dashboard KPI values.
```json
{
  "type": "KPI_UPDATE",
  "payload": {
    "machines_active": 18,
    "operators_active": 16,
    "safety_score": 91.0,
    "machine_health": 94.0,
    "productivity": 87.0,
    "active_alerts": 3,
    "incidents_today": 1
  }
}
```

### PING
```json
{ "type": "PING", "payload": { "ts": "2024-01-15T08:42:00Z" } }
```

---

## Client → Server Events

### ACKNOWLEDGE_ALERT
```json
{
  "type": "ACKNOWLEDGE_ALERT",
  "payload": {
    "alert_id": "uuid",
    "note": "Operator acknowledged — stopped machine"
  }
}
```

### SUBSCRIBE
Subscribe to specific event channels (default: all).
```json
{
  "type": "SUBSCRIBE",
  "payload": {
    "channels": ["ALERT", "TELEMETRY_UPDATE", "KPI_UPDATE"]
  }
}
```

### PONG
```json
{ "type": "PONG", "payload": { "ts": "2024-01-15T08:42:00Z" } }
```

---

## Alert Types Reference

| alert_type | trigger | default_severity |
|------------|---------|-----------------|
| SEATBELT_UNFASTENED | seatbelt off while moving | HIGH |
| PROXIMITY_WARNING | distance < 10m | MEDIUM |
| PROXIMITY_CRITICAL | distance < 5m | CRITICAL |
| SPEED_VIOLATION | speed > zone limit | HIGH |
| OVERLOAD_WARNING | load > 90% | MEDIUM |
| OVERLOAD_CRITICAL | load > 100% | CRITICAL |
| ENGINE_TEMP_WARNING | temp > 105°C | MEDIUM |
| ENGINE_TEMP_CRITICAL | temp > 115°C | CRITICAL |
| HYDRAULIC_WARNING | pressure out of range | MEDIUM |
| EXCESSIVE_IDLING | idle > 15 min | LOW |
| BREAK_RECOMMENDATION | operating > 90 min | LOW |
| DASHCAM_PERSON_ZONE | person in restricted zone | HIGH |
| CERT_EXPIRED | certification expired | HIGH |
| FATIGUE_RISK | fatigue_risk_indicator > 0.75 | MEDIUM |
| MAINTENANCE_DUE | service overdue | MEDIUM |
| UNUSUAL_BEHAVIOUR | anomaly detected | MEDIUM |

---

## Severity → Watch Behaviour

| severity | watch action | vibration pattern |
|----------|-------------|-------------------|
| LOW | notification dot | none |
| MEDIUM | notification screen | single 200ms pulse |
| HIGH | navigate to alert screen | double pulse 300ms |
| CRITICAL | navigate to alert screen + pulse animation | 500,100,500ms |
