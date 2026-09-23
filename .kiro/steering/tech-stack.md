# Tech Stack & Conventions

## Frontend
- **React 18** + **TypeScript**
- **Vite** (build tool)
- **Tailwind CSS** (styling — industrial/enterprise palette: slate, amber, red, green)
- **Recharts** (charts — lightweight, composable)
- **React Router v6** (routing)
- **Zustand** (global state — lightweight, no boilerplate)
- **React Query / TanStack Query** (server state, caching)
- **qrcode.react** (QR code generation)
- **lucide-react** (icons)
- **date-fns** (date formatting)

**Do NOT use:** Redux, MUI, Ant Design, Bootstrap, Axios (use fetch/React Query).

## Backend
- **Python 3.11+**
- **FastAPI** (main framework)
- **Pydantic v2** (validation/schemas)
- **SQLAlchemy 2.0** (ORM, async)
- **Alembic** (migrations)
- **asyncpg** (PostgreSQL async driver)
- **python-jose** (JWT)
- **passlib[bcrypt]** (password hashing)
- **redis** + **aioredis** (cache + pub/sub)
- **websockets** (real-time events)
- **uvicorn** (ASGI server)

**Fallback:** SQLite via aiosqlite for DEMO profile when PostgreSQL unavailable.

## Database
- **PostgreSQL 15** (primary)
- **Redis 7** (cache, pub/sub, real-time event bus)

## ML / AI
- **Python 3.11+**
- **pandas**, **numpy** (data manipulation)
- **scikit-learn** (RandomForestRegressor for ETA, IsolationForest for anomaly)
- **joblib** (model serialization)
- **Faker** (synthetic PII data)
- **pyarrow** / **fastparquet** (Parquet output)

## CV
- **OpenCV** (optional — only if reliable)
- **Simulated CV event adapter** (primary for MVP — no GPU required)

## RAG
- **sentence-transformers** (embeddings)
- **chromadb** (local vector store — no server required)
- **LLM**: configurable via `LLM_PROVIDER` env var (openai / local / mock)

## Auth
- JWT Bearer tokens
- RBAC: operator / supervisor / engineer / safety_officer / maintenance_engineer / admin

## QR
- `qrcode` (Python, for server-side generation)
- `qrcode.react` (frontend display)

## Testing
- **pytest** + **httpx** (backend)
- **vitest** (frontend)

## Conventions

### File naming
- Backend: `snake_case.py`
- Frontend: `PascalCase.tsx` for components, `camelCase.ts` for hooks/utils
- DB models: singular noun (`Operator`, `Machine`, `Task`)
- API routes: plural noun (`/operators`, `/machines`, `/tasks`)

### API responses
Always wrap in: `{ "data": ..., "meta": { "timestamp": ..., "total": ... } }`
Errors: `{ "error": { "code": "...", "message": "..." } }`

### Environment variables
All secrets via `.env` files. Never hardcode. See `backend/.env.example`.

### Commit messages
`feat(frontend):`, `feat(backend):`, `feat(ai):`, `fix:`, `docs:`, `test:`

### Branch strategy
`main` ← `dev` ← `feature/frontend`, `feature/backend`, `feature/ai`
