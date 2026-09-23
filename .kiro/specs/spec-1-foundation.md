# Spec 1 — Foundation, Architecture & Repository

## Status: READY FOR IMPLEMENTATION

---

## Requirements

### REQ-1.1 Monorepo structure
The repository shall use a monorepo layout with top-level folders: `frontend/`, `backend/`, `ml/`, `data/`, `rag/`, `cv/`, `docs/`, `.kiro/`.

### REQ-1.2 Environment configuration
- `backend/.env.example` shall document all required environment variables
- No secrets shall be hardcoded in source files
- Database URL, JWT secret, Redis URL, LLM provider key shall all be env vars

### REQ-1.3 Docker Compose
- `docker-compose.yml` at root shall start: PostgreSQL 15, Redis 7, backend (FastAPI), frontend (Vite dev server)
- Each service shall have health checks
- Volumes shall persist PostgreSQL data

### REQ-1.4 Backend bootstrap
- FastAPI app factory in `backend/app/main.py`
- CORS configured for localhost frontend origin
- `/health` endpoint returning `{ status: "ok", version: "1.0.0" }`
- Lifespan handler for DB connection pool and Redis connection

### REQ-1.5 Frontend bootstrap
- Vite + React 18 + TypeScript project in `frontend/`
- Tailwind CSS configured with custom CAT colour palette
- React Router v6 with all required routes defined (even if pages are stubs)
- Global layout: sidebar navigation + topbar + main content area

### REQ-1.6 Shared contracts
- `docs/api-contracts.md` defines all API response shapes
- `docs/event-schemas.md` defines all WebSocket event types
- `frontend/src/types/` mirrors backend Pydantic schemas as TypeScript interfaces

---

## Design

### Directory layout
```
/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/        # config, database, security, dependencies
│   │   ├── models/      # SQLAlchemy ORM
│   │   ├── schemas/     # Pydantic
│   │   ├── routers/     # FastAPI routers
│   │   ├── services/    # business logic
│   │   └── middleware/  # CORS, audit logging
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── ml/
├── data/
├── rag/
├── cv/
├── docs/
├── docker-compose.yml
├── .gitignore
└── README.md
```

### FastAPI app structure
- Single app instance, all routers mounted under `/api/v1`
- Middleware stack: CORS → audit logging → error handler
- Database: async SQLAlchemy with connection pool

---

## Tasks

- [x] Create monorepo directory structure
- [x] Create .gitignore
- [ ] Create backend/requirements.txt
- [ ] Create backend/.env.example
- [ ] Create backend/app/main.py
- [ ] Create backend/app/core/config.py
- [ ] Create backend/app/core/database.py
- [ ] Create docker-compose.yml
- [ ] Scaffold frontend with Vite
- [ ] Configure Tailwind CSS
- [ ] Create frontend/src/types/ shared interfaces
- [ ] Create docs/api-contracts.md
- [ ] Create docs/event-schemas.md
