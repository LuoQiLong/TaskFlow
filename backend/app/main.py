from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import pyodbc

from .config import CORS_ORIGINS, DB_NAME, _build_conn_str
from .database import engine, Base
from .models.user import User  # noqa: F401 — ensure models are imported for table creation
from .models.task import Task  # noqa: F401
from .models.work import Project, WorkItem, WorkLog, Milestone, WeeklyTarget  # noqa: F401
from .routers import auth, tasks, stats, projects, work_items, work_logs, work_stats, milestones, weekly_targets, admin

# Auto-create database if it doesn't exist
_raw_conn = pyodbc.connect(_build_conn_str("master"), autocommit=True)
_cursor = _raw_conn.cursor()
_cursor.execute(f"SELECT COUNT(*) FROM sys.databases WHERE name = '{DB_NAME}'")
if _cursor.fetchone()[0] == 0:
    _cursor.execute(f"CREATE DATABASE [{DB_NAME}]")
_raw_conn.close()
del _raw_conn, _cursor

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# Helper: add missing columns to existing databases
def _ensure_columns(table: str, columns: list[tuple[str, str]]):
    """Try ALTER TABLE ADD for each column; ignore errors if column already exists."""
    conn = pyodbc.connect(_build_conn_str(DB_NAME), autocommit=True)
    cur = conn.cursor()
    for col_name, col_def in columns:
        try:
            cur.execute(f"ALTER TABLE [{table}] ADD [{col_name}] {col_def}")
        except Exception:
            pass
    conn.close()

_ensure_columns("users", [
    ("role", "VARCHAR(20) NOT NULL DEFAULT 'member'"),
    ("display_name", "VARCHAR(100) NULL"),
    ("is_active", "BIT NOT NULL DEFAULT 1"),
    ("avatar_url", "VARCHAR(500) NULL"),
])
_ensure_columns("work_items", [
    ("attachments", "TEXT NULL"),
    ("week_end", "DATE NULL"),
    ("week_hours", "TEXT NULL"),
    ("completed_weeks", "TEXT NULL"),
])
_ensure_columns("milestones", [
    ("week_start", "DATE NULL"),
])
_ensure_columns("tasks", [
    ("attachments", "TEXT NULL"),
])

app = FastAPI(
    title="TaskFlow API",
    description="TaskFlow 任务管理看板 — Backend API",
    version="1.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(stats.router)
app.include_router(projects.router)
app.include_router(work_items.router)
app.include_router(work_logs.router)
app.include_router(work_stats.router)
app.include_router(milestones.router)
app.include_router(weekly_targets.router)
app.include_router(admin.router)

# Static files for avatar images & work-item uploads
_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(os.path.join(_static_dir, "avatars"), exist_ok=True)
os.makedirs(os.path.join(_static_dir, "work-images"), exist_ok=True)
os.makedirs(os.path.join(_static_dir, "work-attachments"), exist_ok=True)
os.makedirs(os.path.join(_static_dir, "task-images"), exist_ok=True)
os.makedirs(os.path.join(_static_dir, "task-attachments"), exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "TaskFlow API"}
