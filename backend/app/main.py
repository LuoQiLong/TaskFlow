from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .database import engine, Base
from .models.user import User  # noqa: F401 — ensure models are imported for table creation
from .models.task import Task  # noqa: F401
from .models.work import Project, WorkItem, WorkLog, Milestone, WeeklyTarget  # noqa: F401
from .routers import auth, tasks, stats, projects, work_items, work_logs, work_stats, milestones, weekly_targets

# Create all tables on startup
Base.metadata.create_all(bind=engine)

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


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "TaskFlow API"}
