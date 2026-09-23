# Coding Conventions & Rules

## General Rules

- Always read existing code before writing new code in that file
- Match project style — do not introduce new libraries without team agreement
- Every API must have a corresponding Pydantic schema
- Every DB model must have a corresponding schema (request + response)
- Never hardcode secrets, IDs, or thresholds — use config/env
- All thresholds (safety limits, score weights) must be in a single config file: `backend/app/core/config.py`

## Backend Rules

### Structure
```
backend/app/
  main.py           # FastAPI app factory
  core/
    config.py       # all settings via pydantic-settings
    database.py     # SQLAlchemy async engine + session
    security.py     # JWT, password hashing
    dependencies.py # FastAPI Depends() helpers
  models/           # SQLAlchemy ORM models (one file per domain)
  schemas/          # Pydantic request/response schemas
  routers/          # FastAPI routers (one file per domain)
  services/         # Business logic (one file per domain)
  middleware/       # CORS, logging, audit
```

### Safety Engine
- Rule-based engine lives in `backend/app/services/safety_engine.py`
- Rules are pure functions: `def check_proximity(distance: float, threshold: float) -> Alert | None`
- Every rule returns None (no alert) or an Alert dict
- Safety scores are computed in `backend/app/services/scoring.py`
- Score components must be individually accessible, not just the total

### API conventions
- All timestamps: ISO 8601 UTC strings
- All IDs: string UUIDs
- Pagination: `?page=1&page_size=50`
- Filtering: `?machine_id=...&operator_id=...&from_ts=...&to_ts=...`
- Auth: `Authorization: Bearer <token>` header

### RBAC
- Enforce at router level with `Depends(require_role(["engineer", "admin"]))`
- Never rely on frontend to enforce permissions
- Role hierarchy: admin > engineer > supervisor > safety_officer > maintenance_engineer > operator

## Frontend Rules

### Structure
```
frontend/src/
  pages/            # Route-level components (one per route)
  components/
    ui/             # Reusable primitives (Card, Badge, StatusDot, etc.)
    dashboard/      # Dashboard-specific composed components
    watch/          # Watch simulator components
  hooks/            # Custom React hooks (useAlerts, useMachineHealth, etc.)
  services/         # API call functions (not hooks)
  store/            # Zustand stores
  types/            # TypeScript interfaces mirroring backend schemas
  utils/            # Pure utility functions
```

### Component rules
- Every KPI card MUST be clickable and open a detail panel/drawer
- Use `StatusDot` component for all live status indicators (green/amber/red)
- All charts use Recharts — no other chart library
- All tables must support sorting and basic filtering
- Watch UI: max width 320px, dark theme, large text, touch-friendly
- No inline styles — Tailwind only
- Accessibility: all interactive elements must have aria-labels

### Color palette (Tailwind classes)
- Background: `bg-slate-900`, `bg-slate-800`, `bg-slate-700`
- Cards: `bg-slate-800 border border-slate-700`
- Accent / CAT yellow: `bg-amber-500`, `text-amber-400`
- Success / Safe: `text-green-400`, `bg-green-900/30`
- Warning: `text-yellow-400`, `bg-yellow-900/30`
- Danger / Critical: `text-red-400`, `bg-red-900/30`
- Text primary: `text-slate-100`
- Text secondary: `text-slate-400`

### Real-time
- WebSocket connection managed in `src/hooks/useWebSocket.ts`
- Incoming events update Zustand store
- Components subscribe to store, not directly to WebSocket

## ML Rules

### Model files
- Each model: train script + inference script + saved `.joblib` file
- Models live in `ml/models/`
- Training scripts: `ml/training/train_*.py`
- Inference: `ml/inference/predict_*.py`
- All models must work with the demo-size dataset (no GPU required)

### Outputs
- ETA prediction: returns `{ predicted_minutes: float, confidence_interval: [float, float] }`
- Anomaly: returns `{ score: float, label: "NORMAL"|"UNUSUAL", reason: str }`
- Machine health: returns `{ overall: float, components: { engine: float, fuel: float, ... } }`

## Dataset Generator Rules

- Entry point: `python data/generators/generate_data.py --profile demo|dev|stress --seed 42`
- Profiles defined in `data/generators/profiles.py`
- All entities have referential integrity (no orphan foreign keys)
- Output: PostgreSQL seed SQL + Parquet for telemetry
- Seed file: `data/seed/demo_seed.sql` (committed, small, human-readable)
- Large files: `data/generated/` (gitignored)

## Privacy & Safety Labelling Rules

- All biometric fields labelled as "operational risk indicator — not a medical diagnosis"
- `heart_rate`, `fatigue_risk_indicator`, `attention_risk_indicator` — never claim diagnostic accuracy
- `breathalyzer_status` only appears when explicitly flagged as simulated separate sensor
- QR codes contain only `operator_id` — no biometric or personal data
- Audit logs are write-only from the application (no delete endpoint)
