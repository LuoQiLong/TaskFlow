from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    due_date: Optional[datetime] = None
    assignee: Optional[str] = None
    tags: list[str] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(todo|in_progress|done)$")
    priority: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")
    column_order: Optional[int] = None
    due_date: Optional[datetime] = None
    assignee: Optional[str] = None
    tags: Optional[list[str]] = None


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(todo|in_progress|done)$")
    column_order: int = Field(ge=0)


class ReorderItem(BaseModel):
    id: int
    status: str = Field(pattern="^(todo|in_progress|done)$")
    column_order: int = Field(ge=0)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    column_order: int
    due_date: Optional[str] = None
    assignee: Optional[str] = None
    tags: list[str] = []
    user_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}
