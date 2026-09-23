# Spec 2 — Database Schema & Dataset Generator

## Status: READY FOR IMPLEMENTATION

---

## Requirements

### REQ-2.1 PostgreSQL schema
All 34 entities from the master prompt shall have corresponding SQLAlchemy models and Alembic migrations.

Core entities (P0):
- sites, zones, operators, machines, machine_models
- tasks, task_assignments, task_events
- telemetry (partitioned by day if practical, else plain table)
- safety_events, alerts, alert_acknowledgements
- incidents, prestart_checks, machine_permissions
- operator_breaks, audit_logs, notifications
- wearable_events, dashcam_events, proximity_events
- environmental_data, fuel_events
- users (auth), roles

Extended entities (P1):
- operator_certifications, operator_training, machine_maintenance
- machine_faults, productivity_metrics, anomaly_scores
- task_predictions, maintenance_predictions
- training_recommendations, watch_events

### REQ-2.2 Dataset generator
- Entry point: `python data/generators/generate_data.py --profile demo|dev|stress --seed 42`
- Profiles: demo (10 operators, 10 machines, 2 sites, ~5k telemetry rows), dev (100/50/5/100k), stress (500/200/20/1M+)
- All data is synthetic and reproducible with the same seed
- Referential integrity enforced — no orphan FKs
- Output: SQL INSERT statements to `data/seed/demo_seed.sql` + Parquet for telemetry

### REQ-2.3 Data realism
- Engine hours increment monotonically over time
- Fuel consumption correlates with engine load
- Weather affects task duration (rain → slower)
- Operator skill level affects task speed
- Machine age increases maintenance risk probability
- Faults cluster after high-load periods
- Anomaly events are statistically unusual (inserted deliberately, not randomly)
- Proximity events trigger corresponding safety_events and alerts

### REQ-2.4 Demo seed
`data/seed/demo_seed.sql` shall be committed and small enough to load in <5 seconds.
It shall contain exactly the DEMO profile data with seed=42.

### REQ-2.5 Demo scenario data
Generator shall accept `--scenario` flag to inject specific scenarios:
- normal_operation, proximity_hazard, seatbelt_violation, excessive_idling
- machine_overheating, hydraulic_anomaly, unusual_operator_behaviour
- extended_shift, dashcam_person_detection, prestart_failure
- maintenance_warning, task_delay_weather

---

## Design

### Key schema decisions
- All PKs: UUID (text in SQLite, uuid in PostgreSQL)
- All timestamps: TIMESTAMP WITH TIME ZONE
- Soft deletes: `is_active` boolean, never hard delete operational records
- Telemetry: one row per machine per minute during active operation

### Telemetry columns (key subset)
```
timestamp, site_id, zone_id, machine_id, operator_id, task_id,
engine_status, engine_rpm (800-2200), engine_temperature (70-120°C),
oil_pressure (30-80 PSI), coolant_temperature (75-100°C), battery_voltage (12-14.8V),
fuel_level (0-100%), fuel_consumption_rate (L/hr), fuel_used (cumulative L),
hydraulic_pressure (bar), hydraulic_temperature (°C), hydraulic_flow (L/min),
machine_speed (km/h), machine_load (0-100%), cycle_count, cycle_time (min),
idle_time (min), operating_hours (cumulative), vibration (g),
fault_code (nullable), maintenance_status
```

### Operator / wearable columns
```
heart_rate (55-180 bpm), heart_rate_delta,
activity_level (0-10), motion_level (0-10),
skin_temperature (35-38°C), wearable_battery (0-100%),
wearable_connected (bool),
attention_risk_indicator (0-1, NOT a medical diagnosis),
fatigue_risk_indicator (0-1, NOT a medical diagnosis),
self_reported_status
```

### Generator architecture
```
data/generators/
  generate_data.py      # CLI entry point
  profiles.py           # demo/dev/stress config dicts
  generators/
    sites.py
    operators.py
    machines.py
    tasks.py
    telemetry.py
    safety_events.py
    wearable_events.py
    dashcam_events.py
    scenarios.py        # inject specific demo scenarios
  writers/
    sql_writer.py
    parquet_writer.py
```

---

## Tasks

- [ ] Create SQLAlchemy models for all P0 entities
- [ ] Create Alembic migration: initial schema
- [ ] Create data/generators/profiles.py
- [ ] Create data/generators/generate_data.py (CLI)
- [ ] Implement site + zone generator
- [ ] Implement operator generator (with realistic names, skill levels, certs)
- [ ] Implement machine generator (with age, model, maintenance history)
- [ ] Implement task generator (with correlated durations)
- [ ] Implement telemetry generator (time-series, correlated values)
- [ ] Implement safety_events + alerts generator
- [ ] Implement wearable_events generator
- [ ] Implement dashcam_events generator (simulated)
- [ ] Implement scenario injector
- [ ] Implement SQL writer
- [ ] Implement Parquet writer
- [ ] Generate and commit data/seed/demo_seed.sql
