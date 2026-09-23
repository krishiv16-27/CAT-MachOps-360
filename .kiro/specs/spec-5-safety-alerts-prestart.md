# Spec 5 — Safety Engine, Alerts & Pre-Start Checklist

## Status: READY FOR IMPLEMENTATION

---

## Requirements

### REQ-5.1 Rule-based safety engine
`backend/app/services/safety_engine.py` shall implement deterministic rules:

| Rule | Trigger | Severity |
|------|---------|----------|
| seatbelt_unfastened | seatbelt = UNFASTENED while moving | HIGH |
| proximity_warning | person_distance < warning_threshold (default 10m) | MEDIUM |
| proximity_critical | person_distance < critical_threshold (default 5m) | CRITICAL |
| speed_violation | speed > speed_limit for zone | HIGH |
| overload_warning | machine_load > 90% | MEDIUM |
| overload_critical | machine_load > 100% | CRITICAL |
| engine_temperature_warning | engine_temp > 105°C | MEDIUM |
| engine_temperature_critical | engine_temp > 115°C | CRITICAL |
| hydraulic_pressure_warning | hydraulic_pressure outside ±20% of nominal | MEDIUM |
| excessive_idling | idle_duration > 15 min continuous | LOW |
| shift_break_recommendation | continuous_operating_minutes > 90 | LOW |
| dashcam_person_zone | person detected in restricted zone | HIGH |
| certification_expired | operator cert expiry < today | HIGH |
| fatigue_risk | fatigue_risk_indicator > 0.75 | MEDIUM |

All thresholds configurable via `backend/app/core/config.py`.

### REQ-5.2 Alert record
Every triggered rule creates an alert with:
```
alert_id, timestamp, site_id, zone_id, machine_id, operator_id, task_id,
alert_type, severity (LOW/MEDIUM/HIGH/CRITICAL),
trigger_data (JSON), message, recommended_action,
acknowledged (bool), acknowledged_by, acknowledged_at,
resolved (bool), resolved_at
```

### REQ-5.3 Alert API
- `GET /alerts` — paginated, filterable by severity/machine/operator/date/resolved
- `GET /alerts/:id` — single alert detail
- `POST /alerts/:id/acknowledge` — operator or supervisor acknowledges
- `POST /alerts` — internal (safety engine posts alerts)
- WebSocket broadcasts every new alert to all connected clients

### REQ-5.4 Pre-start checklist (`/prestart`)
Before machine assignment, operator/supervisor completes checklist.
Checklist items (all required unless marked optional):
1. Operator authenticated
2. Operator authorized for machine type
3. Certification valid and not expired
4. Seatbelt functional (self-reported)
5. Fuel level ≥ 20%
6. Machine health check passed (no CRITICAL faults)
7. No critical active fault codes
8. Safety zone clear (supervisor confirms)
9. Emergency stop system available (self-reported)
10. Required training completed for machine type
11. Wearable device connected (optional)

Authorization outcomes:
- **AUTHORIZED** — all required checks pass
- **BLOCKED** — any required check fails (shows which item failed)
- **REVIEW** — optional items failed or risk indicators elevated (supervisor can override)

Pre-start record stored in `prestart_checks` table.
Machine `authorization_status` updated in `machine_permissions`.

### REQ-5.5 Safety score
Computed in `backend/app/services/scoring.py`:
```
safety_score = weighted sum of:
  seatbelt_compliance_rate     (weight: 0.25)
  proximity_event_rate         (weight: 0.20)
  speed_violation_rate         (weight: 0.15)
  incident_rate                (weight: 0.20)
  pre_start_compliance_rate    (weight: 0.10)
  training_completion_rate     (weight: 0.10)
```
Score: 0–100. Labelled "Operational Safety Score (Demo Index)".
Each component accessible individually via `/operators/:id/safety-score`.

### REQ-5.6 Incident logging
Every CRITICAL alert auto-creates an incident draft.
Manual incident creation via `POST /incidents`.
Incident fields: incident_id, timestamp, site, zone, machine, operator, task,
category, severity, description, trigger_data, evidence (JSON list),
status (OPEN/INVESTIGATING/RESOLVED), assigned_to, resolution,
root_cause, corrective_action.

---

## Design

### Safety engine flow
```
Telemetry/event ingested
  → safety_engine.evaluate(event)
    → run all applicable rules
    → collect triggered alerts
  → for each alert:
      → INSERT into alerts table
      → publish to Redis channel "alerts"
      → WebSocket broadcaster picks up + pushes to clients
      → if CRITICAL: auto-create incident draft
```

### Pre-start checklist UI
```
┌─────────────────────────────────────┐
│  PRE-START MACHINE CHECK            │
│  Machine: EXC001   Operator: OP1001 │
├─────────────────────────────────────┤
│  [✓] Operator authenticated         │
│  [✓] Operator authorized            │
│  [✓] Certification valid            │
│  [✓] Seatbelt functional            │
│  [✓] Fuel ≥ 20%  (current: 67%)    │
│  [✓] Machine health: PASS           │
│  [✓] No critical faults             │
│  [✓] Safety zone clear              │
│  [✓] Emergency stop available       │
│  [✓] Required training complete     │
│  [~] Wearable connected (optional)  │
├─────────────────────────────────────┤
│  ✅ AUTHORIZED — All checks passed  │
│  [START MACHINE SESSION]            │
└─────────────────────────────────────┘
```

Blocked state shows red item with reason:
```
│  [✗] Certification valid            │
│      EXPIRED: 2024-01-15           │
│  ─────────────────────────────────  │
│  🚫 BLOCKED — Certification expired │
```

---

## Tasks

- [ ] Create safety_engine.py with all 14 rules
- [ ] Create scoring.py (safety score computation)
- [ ] Create Alert SQLAlchemy model + Pydantic schemas
- [ ] Create Incident SQLAlchemy model + Pydantic schemas
- [ ] Create PrestartCheck SQLAlchemy model
- [ ] Create MachinePermission model
- [ ] Create alerts router (GET, POST, PATCH acknowledge)
- [ ] Create incidents router (GET, POST, PATCH)
- [ ] Create prestart router (GET checklist, POST submit)
- [ ] Create safety score endpoint
- [ ] Create Redis publisher for alert events
- [ ] Create WebSocket broadcaster
- [ ] Create frontend alerts page (/alerts)
- [ ] Create alert severity badge component
- [ ] Create frontend pre-start checklist page (/prestart)
- [ ] Create frontend incidents page (/incidents)
- [ ] Create safety score drilldown component
- [ ] Wire alert → watch notification flow
