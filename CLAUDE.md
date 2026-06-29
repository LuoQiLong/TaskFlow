# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaskFlow is a dual-module task management kanban board with Chinese UI.

- **Kanban module** — three-column drag-and-drop task board (todo / in_progress / done) with filtering, archiving, overdue detection, rich-text description (TiptapEditor), file attachments, and stats
- **Work Weekly module** — project-based tasks/work-orders with hour tracking, milestones, saturation stats (40h/week default, per-week customizable targets), cross-week splitting, rich-text description, file attachments, and a dashboard

**Stack**: FastAPI + SQLAlchemy + SQL Server / SQLite (backend) / Vue 3 + TypeScript + Vite + Element Plus + Pinia + ECharts + Tiptap (rich text) + xlsx-js-style (frontend)

## Common Commands

```bash
# Backend (port 8000)
cd backend
cp .env.example .env          # first time only — edit SECRET_KEY for production
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (port 5173, proxies /api + /static → localhost:8000)
cd frontend
npm install
npm run dev        # dev server
npm run build      # type-check (vue-tsc -b) + vite build
npm run preview    # serve production build locally
```

Backend Swagger docs: `http://localhost:8000/docs`

Environment variables (optional, with defaults in `backend/app/config.py`):
- `TASKFLOW_SECRET_KEY` — JWT signing key (default: dev key, **change in production**)
- `TASKFLOW_DB_HOST` / `_PORT` / `_USER` / `_PASSWORD` / `_NAME` / `_DRIVER` — SQL Server connection (defaults: `LQL`, empty port, `sa`, `123`, `taskflow`, `ODBC Driver 18 for SQL Server`). The code does NOT read `TASKFLOW_DATABASE_URL` — it always builds a `mssql+pyodbc` URL from the individual params. Note: `.env.example` incorrectly references `TASKFLOW_DATABASE_URL` (SQLite fallback) — this is not honored by `config.py`.
- `TASKFLOW_SMTP_HOST` / `_PORT` / `_USER` / `_PASSWORD` — QQ SMTP for password reset emails

## Architecture

### Backend

```
backend/app/
  main.py              # FastAPI app, CORS, router registration, DB auto-create + migration
  config.py            # SECRET_KEY, DATABASE_URL, CORS_ORIGINS, SMTP config
  database.py          # SQLAlchemy engine + SessionLocal + get_db dependency
  middleware/auth.py   # get_current_user (JWT type guard, is_active check), require_admin, resolve_target_user
  models/              # SQLAlchemy ORM models (User, Task, Project, WorkItem, WorkLog, Milestone, WeeklyTarget)
  schemas/             # Pydantic v2 models for request/response validation
  routers/             # 10 route modules (auth, tasks, stats, projects, work_items, work_logs, work_stats, milestones, weekly_targets, admin)
  utils/security.py    # bcrypt password hashing + JWT create/decode + password reset tokens
  utils/email.py       # QQ SMTP email sending for password reset
```

- All routes are user-scoped via `current_user: User = Depends(get_current_user)`
- JWT uses `python-jose` with `HS256`, 24h expiry; reset tokens use 15min expiry with `type: "password_reset"` claim
- Pydantic response models use `model_config = {"from_attributes": True}` for ORM compatibility
- All timestamps use `datetime.now()` (Beijing time), NOT UTC
- `resolve_target_user(current_user, target_user_id)` helper for admin scope switching across all routes
- User roles: `admin` / `member`; first admin designated manually in database
- **Startup**: `main.py` auto-creates the SQL Server database (via pyodbc to `master`), then runs `Base.metadata.create_all()` + ad-hoc `ALTER TABLE` migrations via `_ensure_columns()` helper. No Alembic — migrations are manual. Call `_ensure_columns("table", [("col", "TYPE")])` for new columns.
- **Static files**: Four upload directories auto-created on startup:
  - `static/work-images/` + `static/work-attachments/` — Work Weekly module
  - `static/task-images/` + `static/task-attachments/` — Kanban module
  - `static/avatars/` — user profile photos
  FastAPI mounts `/static` and Vite proxies it.

### Frontend

```
frontend/src/
  main.ts              # App entry: Pinia + Router + Element Plus (zh-CN)
  router/index.ts      # Vue Router with auth guard (checks localStorage 'auth'), guest/forgot routes excluded from redirect
  api/client.ts        # Axios instance: auto Bearer token, 401 → redirect /login
  api/*.ts             # Typed API functions (10 files, one per backend router group)
  stores/              # Pinia stores: auth, task, project, work-item, scope
  layout/AppLayout.vue # Header nav with kanban/dashboard/work-weekly tabs + dark mode + admin scope selector + avatar
  views/
    LoginView.vue        # Login with centered card layout + "忘记密码" link
    RegisterView.vue     # Registration with centered card layout
    ForgotPassword.vue   # Password reset request with email confirmation
    ResetPassword.vue    # Reset password with token from email link
    KanbanView.vue       # Three-column drag-and-drop task board + archive drawer
    DashboardView.vue    # Tabbed dashboard: Kanban stats + Work Weekly charts
    WorkWeeklyView.vue   # Work weekly CRUD with week/month pill toggle + search + milestone progress
    ProfileView.vue      # Personal settings: avatar crop upload, display name, password change
    AdminUsers.vue       # Admin user management: search, role edit, enable/disable, password reset, delete
```

- `@` alias maps to `./src` (configured in vite.config.ts)
- Element Plus uses Chinese locale
- Charts use vue-echarts (BarChart, PieChart, LineChart, HeatmapChart)
- Kanban drag-and-drop is HTML5 native (no library)

### Database (7 tables)

| Table | Purpose |
|-------|---------|
| `users` | User accounts (email + bcrypt password, role, display_name, is_active, avatar_url) |
| `tasks` | Kanban tasks (title, description, status, priority, order, tags, attachments JSON, assignee, due_date) |
| `projects` | Work-weekly projects (name, color) |
| `work_items` | Unified task/work-order model, `type` field distinguishes. Cross-week fields: `week_end`, `week_hours` (JSON), `completed_weeks` (JSON). Also has `attachments` JSON |
| `work_logs` | Hour entries linked to work_items. `is_system` flag for auto-generated logs |
| `milestones` | Milestones linked to work_items. `is_locked` for system-generated, `week_start` for per-week association |
| `weekly_targets` | Per-week target hours (default 40h, unique per user+week) |

Full schema: `backend/DATABASE_SCHEMA.md`

### API Routes

| Prefix | Purpose |
|--------|---------|
| `/api/auth` | Login, register, get current user, forgot/reset password, avatar upload, profile update |
| `/api/tasks` | Kanban task CRUD + reorder + `upload-image`/`upload-attachment`/`images/cleanup` (supports `target_user_id`, `include_archived`) |
| `/api/stats` | Kanban overview + 30-day trend (supports `target_user_id`) |
| `/api/projects` | Project CRUD (user-scoped) |
| `/api/work-items` | Work item CRUD + status change + `upload-image`/`upload-attachment`/`images/cleanup` + tag/week/overdue/search filtering (supports `target_user_id`) |
| `/api/work-logs` | Work log CRUD |
| `/api/work-stats` | Weekly/monthly/trend/dashboard stats (supports `target_user_id` aggregation) |
| `/api/milestones` | Milestone CRUD + reorder |
| `/api/weekly-targets` | Weekly target hours CRUD |
| `/api/admin` | Admin-only: user list/search/filter, update role/status, reset password, delete user |
| `/api/health` | Health check |

## Key Business Rules

1. **Drag to done**: Moving a WorkItem to `done` auto-creates a system WorkLog (`is_system=true`) + locked Milestone. For cross-week items: only completed_ms_hours from the current week are subtracted (`Milestone.week_start == complete_week`).
2. **Drag from done**: Moving out of `done` detaches work_logs from locked milestones, deletes orphan system work_logs, then deletes locked milestones. For cross-week: only affects the current browsing week (JOIN with Milestone to only delete logs linked to locked milestones).
3. **Cross-week details**: `week_hours` JSON `{"2026-06-22":5,"2026-06-29":15}` stores per-week allocation. `completed_weeks` JSON `["2026-06-22"]` tracks which weeks are done. `estimated_hours` auto = sum of week_hours. Frontend `getItemCol()` checks `completed_weeks[ws]` to place item in "done" column only for completed weeks — status stays "done" once any week is complete.
4. **Tags**: Stored as comma-separated TEXT in DB, returned as `string[]` by API (both tasks and work_items)
5. **Work week target**: Default 40 hours/week (`WEEKLY_HOURS = 40` in `work_stats.py`), overridable per-week via `/api/weekly-targets`
6. **Month view**: Uses range query (`week_start_from`/`week_start_to`) with overlap logic (`week_start <= to AND (week_end IS NULL OR week_end >= from)`)
7. **Admin scope**: `target_user_id` — `0`/`null`=self, `-1`=all users, `>0`=specific user; stats aggregate across all users when `-1`
8. **Archived tasks**: `status='archived'` excluded from stats/queries by default; `include_archived=true` to show
9. **Avatar upload**: Canvas-based crop (320×320 crop area, drag to adjust) → 256×256 output, saved to `backend/static/avatars/`
10. **Password reset**: JWT-based (type: `"password_reset"`, 15min expiry) + QQ SMTP HTML email
11. **Rich text editor**: Both KanbanView and WorkWeeklyView use `TiptapEditor` component for description fields. It supports image paste/upload (Ctrl+V), tables, headings, colors, task lists, and link insertion. Accepts `uploadUrl` prop to configure the upload endpoint per module.
12. **File attachments**: Both modules support attachments via drag-and-drop / click-to-upload. Files stored in module-specific directories. Session-level cleanup: orphaned images/attachments from the editing session are deleted when the dialog is cancelled.

## Notable Patterns

- Backend: `to_dict()` method on every model serializes dates/ISO strings, tags to arrays
- Backend: Router responses use `SchemaResponse.model_validate(item.to_dict())` pattern
- Backend: `WeeklyTarget` is a standalone model (not nested under other work models) — per-week target hours with unique constraint on `(week_start, user_id)`
- Backend: `resolve_target_user(current_user, target_user_id)` returns `int | None` — `None` means "all users", raises 403 for non-admins
- Backend: SQL Server doesn't support `func.date()` — use `cast(column, Date)` instead; multi-path CASCADE FKs removed (ORM-level only)
- Backend: `CREATE DATABASE` on SQL Server requires `autocommit=True` via raw pyodbc
- Frontend: `types/index.ts` defines shared `STATUS_MAP`, `PRIORITY_MAP`, `ROLE_MAP` and their `_OPTIONS` arrays used across views
- Frontend: `formatDate()` uses `getFullYear()/getMonth()/getDate()` (local time), NOT `toISOString()`
- Frontend: Month view uses `delete store.filters.week_start` + single range query, NOT per-week fetches
- Frontend: Drag reactivity requires `items.value = [...items.value]` after in-place mutation
- Frontend: Background glows on all authenticated pages via `.app-main { position: relative; z-index }` layers
- Frontend: `scopeStore` persisted to localStorage, all stores inject `target_user_id` from scope when fetching
- Frontend: `TiptapEditor` shared component — pass `upload-url` prop to set per-module image upload endpoint (`/tasks/upload-image` vs `/work-items/upload-image`)
- Frontend: Card descriptions use `stripHtml()` to render plain text from Tiptap HTML — apply when displaying description in cards/lists
- Pydantic: Field named `date` conflicts with `datetime.date` type — use `log_date` or `target_date` instead
- TypeScript: `erasableSyntaxOnly` is enabled in `tsconfig.app.json` (TS 6.0 feature) — forbids `enum`, `namespace`, and constructor parameter properties. Use `Record<string, string>` + `const` objects instead of enums (see `types/index.ts` for the established pattern).
- Auth: Login and Register are separate views with their own routes (`/login`, `/register`), both guarded with `{ guest: true }` meta
- Auth: Forgot/reset password paths excluded from 401 redirect in `client.ts`
- **Timezones**: JWT token expiry uses `datetime.now(timezone.utc)` in `utils/security.py`, but all application data timestamps use `datetime.now()` (Beijing time) in models/routers. Don't mix these — tokens → UTC, data → local.
- **Excel export**: The frontend uses `xlsx-js-style` for client-side Excel export of work items; the export logic lives in `WorkWeeklyView.vue`.
- **`config.py` security**: Database and SMTP credentials are hardcoded as defaults — override via environment variables in production.
