from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from ..database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    color = Column(String(20), nullable=False, default="#6366f1")
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    work_items = relationship("WorkItem", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "description": self.description,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WorkItem(Base):
    __tablename__ = "work_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False, default="task")  # 'task' or 'work_order'
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="todo")
    priority = Column(String(10), nullable=False, default="medium")
    estimated_hours = Column(Float, nullable=True)
    week_start = Column(Date, nullable=False)  # Monday of the week this item belongs to
    is_cross_week = Column(Boolean, nullable=False, default=False)
    tags = Column(Text, nullable=True)  # comma-separated
    column_order = Column(Integer, nullable=False, default=0)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("Project", back_populates="work_items")
    work_logs = relationship("WorkLog", back_populates="work_item", cascade="all, delete-orphan")
    milestones = relationship("Milestone", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_work_items_user_id", "user_id"),
        Index("ix_work_items_project_id", "project_id"),
        Index("ix_work_items_type", "type"),
        Index("ix_work_items_week_start", "week_start"),
        Index("ix_work_items_project_week", "project_id", "week_start"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "week_start": self.week_start.isoformat() if self.week_start else None,
            "is_cross_week": self.is_cross_week,
            "tags": [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags else [],
            "column_order": self.column_order,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkLog(Base):
    __tablename__ = "work_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False)
    week_start = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    log_date = Column(Date, nullable=True)
    note = Column(Text, nullable=True)
    is_system = Column(Boolean, nullable=False, default=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    work_item = relationship("WorkItem", back_populates="work_logs")

    __table_args__ = (
        Index("ix_work_logs_work_item_id", "work_item_id"),
        Index("ix_work_logs_week_start", "week_start"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "work_item_id": self.work_item_id,
            "week_start": self.week_start.isoformat() if self.week_start else None,
            "hours": self.hours,
            "log_date": self.log_date.isoformat() if self.log_date else None,
            "note": self.note,
            "is_system": self.is_system,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hours = Column(Float, nullable=True)
    target_date = Column(Date, nullable=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)
    is_locked = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("ix_milestones_work_item_id", "work_item_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "work_item_id": self.work_item_id,
            "title": self.title,
            "description": self.description,
            "hours": self.hours,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_locked": self.is_locked,
            "sort_order": self.sort_order,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WeeklyTarget(Base):
    __tablename__ = "weekly_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_start = Column(Date, nullable=False)
    target_hours = Column(Float, nullable=False, default=40.0)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        Index("ix_weekly_targets_week_user", "week_start", "user_id", unique=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "week_start": self.week_start.isoformat() if self.week_start else None,
            "target_hours": self.target_hours,
            "user_id": self.user_id,
        }
