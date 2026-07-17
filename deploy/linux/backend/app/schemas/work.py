from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Attachment ──

class AttachmentItem(BaseModel):
    name: str
    url: str
    size: int  # bytes


# ── Project ──

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#6366f1", max_length=20)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    color: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    color: str
    description: Optional[str] = None
    user_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── WorkItem ──

class WorkItemCreate(BaseModel):
    project_id: int
    type: str = Field(default="task", pattern="^(task|work_order)$")
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    estimated_hours: Optional[float] = None
    week_start: date
    is_cross_week: bool = False
    week_end: Optional[date] = None
    week_hours: Optional[dict[str, float]] = None  # {"2026-06-22": 5, ...}
    tags: list[str] = []
    attachments: list[AttachmentItem] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class WorkItemUpdate(BaseModel):
    project_id: Optional[int] = None
    type: Optional[str] = Field(default=None, pattern="^(task|work_order)$")
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(todo|in_progress|done)$")
    priority: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")
    estimated_hours: Optional[float] = None
    week_start: Optional[date] = None
    is_cross_week: Optional[bool] = None
    week_end: Optional[date] = None
    week_hours: Optional[dict[str, float]] = None
    tags: Optional[list[str]] = None
    column_order: Optional[int] = None
    attachments: Optional[list[AttachmentItem]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class WorkItemStatusUpdate(BaseModel):
    status: str = Field(pattern="^(todo|in_progress|done)$")
    column_order: int = Field(ge=0)
    week_start: Optional[date] = None  # for cross-week: which week is being completed


class WorkItemResponse(BaseModel):
    id: int
    project_id: int
    type: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    estimated_hours: Optional[float] = None
    week_start: Optional[date] = None
    week_end: Optional[date] = None
    is_cross_week: bool
    week_hours: Optional[dict[str, float]] = None
    completed_weeks: list[str] = []
    num_weeks: int = 1
    tags: list[str] = []
    column_order: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    attachments: list[AttachmentItem] = []
    due_date: Optional[datetime] = None
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── WorkLog ──

class WorkLogCreate(BaseModel):
    work_item_id: int
    week_start: date
    hours: float = Field(gt=0)
    log_date: Optional[date] = None
    note: Optional[str] = None


class WorkLogUpdate(BaseModel):
    hours: Optional[float] = Field(default=None, gt=0)
    log_date: Optional[date] = None
    note: Optional[str] = None


class WorkLogResponse(BaseModel):
    id: int
    work_item_id: int
    week_start: Optional[date] = None
    hours: float
    log_date: Optional[date] = None
    note: Optional[str] = None
    is_system: bool = False
    user_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Milestone ──

class MilestoneCreate(BaseModel):
    work_item_id: int
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    hours: Optional[float] = None
    target_date: Optional[date] = None
    week_start: Optional[date] = None  # for cross-week: which week this manual milestone belongs to


class MilestoneUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    hours: Optional[float] = None
    target_date: Optional[date] = None
    is_completed: Optional[bool] = None
    week_start: Optional[date] = None
    sort_order: Optional[int] = None


class MilestoneResponse(BaseModel):
    id: int
    work_item_id: int
    title: str
    description: Optional[str] = None
    hours: Optional[float] = None
    target_date: Optional[date] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    is_locked: bool = False
    week_start: Optional[date] = None
    sort_order: int
    user_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
