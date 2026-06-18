# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaskFlow is a dual-module task management kanban board with Chinese UI.

- **Kanban module** — three-column drag-and-drop task board (todo / in_progress / done) with filtering, archiving, overdue detection, and basic stats
- **Work Weekly module** — project-based tasks/work-orders with hour tracking, milestones, saturation stats (40h/week default, per-week customizable targets), cross-week splitting, and a dashboard

**Stack**: FastAPI + SQLAlchemy + SQLite (backend) / Vue 3 + TypeScript + Vite + Element Plus + Pinia + ECharts (frontend)

## Common Commands

```bash
# Backend (port 8000)
cd backend
cp .env.example .env          # first time only — edit SECRET_KEY for production
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (port 5173, proxies /api → localhost:8000)
cd frontend
npm install
npm run dev        # dev server
npm run build      # type-check + vite build
```

Backend Swagger docs: `http://localhost:8000/docs`

Environment variables (optional, with defaults in `backend/app/config.py`):
- `TASKFLOW_SECRET_KEY` — JWT signing key (default: dev key, **change in production**)
- `TASKFLOW_DATABASE_URL` — SQLite path (default: `sqlite:///./taskflow.db`)

## Architecture

### Backend

```
backend/app/
  main.py              # FastAPI app, CORS, router registration, Base.metadata.create_all
  config.py            # SECRET_KEY, DATABASE_URL (SQLite), CORS_ORIGINS
  database.py          # SQLAlchemy engine + SessionLocal + get_db dependency
  middleware/auth.py   # get_current_user: Bearer JWT → user lookup
  models/              # SQLAlchemy ORM models (User, Task, Project, WorkItem, WorkLog, Milestone, WeeklyTarget)
  schemas/             # Pydantic v2 models for request/response validation
  routers/             # 9 route modules (auth, tasks, stats, projects, work_items, work_logs, work_stats, milestones, weekly_targets)
  utils/security.py    # bcrypt password hashing + JWT create/decode
```

- All routes are user-scoped via `current_user: User = Depends(get_current_user)`
- JWT uses `python-jose` with `HS256`, 24h expiry, no refresh mechanism
- Pydantic response models use `model_config = {"from_attributes": True}` for ORM compatibility
- All timestamps use `datetime.now()` (Beijing time), NOT UTC
- SQLite with WAL mode + foreign key PRAGMAs enabled

### Frontend

```
frontend/src/
  main.ts              # App entry: Pinia + Router + Element Plus (zh-CN)
  router/index.ts      # Vue Router with auth guard (checks localStorage 'auth')
  api/client.ts        # Axios instance: auto Bearer token, 401 → redirect /login
  api/*.ts             # Typed API functions (9 files, one per backend router group)
  stores/              # Pinia stores: auth, task, project, work-item
  layout/AppLayout.vue # Header nav with kanban/dashboard/work-weekly tabs + dark mode
  views/
    LoginView.vue        # Login with centered card layout
    RegisterView.vue     # Registration with centered card layout
    KanbanView.vue       # Three-column drag-and-drop task board
    DashboardView.vue    # Tabbed dashboard: Kanban stats + Work Weekly charts
    WorkWeeklyView.vue   # Work weekly CRUD with week/month view toggle
```

- `@` alias maps to `./src` (configured in vite.config.ts)
- Element Plus uses Chinese locale
- Charts use vue-echarts (BarChart, PieChart, LineChart, HeatmapChart)
- Kanban drag-and-drop is HTML5 native (no library)

### Database (7 tables)

| Table | Purpose |
|-------|---------|
| `users` | User accounts (email + bcrypt password) |
| `tasks` | Simple kanban tasks (title, status, priority, order, tags) |
| `projects` | Work-weekly projects (name, color) |
| `work_items` | Unified task/work-order model, `type` field distinguishes |
| `work_logs` | Hour entries linked to work_items |
| `milestones` | Milestones linked to work_items (can be locked/system-generated) |
| `weekly_targets` | Per-week target hours (default 40h, unique per user+week) |

Full schema: `backend/DATABASE_SCHEMA.md`

### API Routes

| Prefix | Purpose |
|--------|---------|
| `/api/auth` | Login, register, get current user |
| `/api/tasks` | Kanban task CRUD + reorder |
| `/api/stats` | Kanban overview + 30-day trend |
| `/api/projects` | Project CRUD |
| `/api/work-items` | Work item CRUD + status change + tag/week/overdue filtering |
| `/api/work-logs` | Work log CRUD |
| `/api/work-stats` | Weekly/monthly/trend/dashboard stats |
| `/api/milestones` | Milestone CRUD + reorder |
| `/api/weekly-targets` | Weekly target hours CRUD |
| `/api/health` | Health check |

## Key Business Rules

1. **Drag to done**: Moving a WorkItem to `done` auto-creates a system WorkLog (`is_system=true`) + locked Milestone
2. **Drag from done**: Moving out of `done` deletes the auto-created system logs and locked milestones
3. **Tags**: Stored as comma-separated TEXT in DB, returned as `string[]` by API (both tasks and work_items)
4. **Work week target**: Default 40 hours/week (`WEEKLY_HOURS = 40` in `work_stats.py`), overridable per-week via `/api/weekly-targets`
5. **Cross-week**: `WorkItem.is_cross_week` marks items spanning multiple weeks
6. **Month view**: Uses range query (`week_start_from`/`week_start_to`) with `elif` for exclusive OR against exact `week_start`

## Notable Patterns

- Backend: `to_dict()` method on every model serializes dates/ISO strings, tags to arrays
- Backend: Router responses use `SchemaResponse.model_validate(item.to_dict())` pattern
- Backend: `WeeklyTarget` is a standalone model (not nested under other work models) — per-week target hours with unique constraint on `(week_start, user_id)`
- Frontend: `types/index.ts` defines shared `STATUS_MAP`, `PRIORITY_MAP` and their `_OPTIONS` arrays used across views
- Frontend: `formatDate()` uses `getFullYear()/getMonth()/getDate()` (local time), NOT `toISOString()`
- Frontend: Month view uses `delete store.filters.week_start` + single range query, NOT per-week fetches
- Frontend: Drag reactivity requires `items.value = [...items.value]` after in-place mutation
- Pydantic: Field named `date` conflicts with `datetime.date` type — use `log_date` or `target_date` instead
- TypeScript: `erasableSyntaxOnly` is enabled in `tsconfig.app.json` (TS 6.0 feature — only allows type annotations that can be erased at compile time)
- Auth: Login and Register are separate views with their own routes (`/login`, `/register`), both guarded with `{ guest: true }` meta
