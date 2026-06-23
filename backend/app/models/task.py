from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from ..database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(20),
        nullable=False,
        default="todo",
    )
    priority = Column(
        String(10),
        nullable=False,
        default="medium",
    )
    column_order = Column(Integer, nullable=False, default=0)
    due_date = Column(DateTime, nullable=True)
    assignee = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)  # comma-separated tags
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    owner = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index("ix_tasks_user_id", "user_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_user_status_order", "user_id", "status", "column_order"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "column_order": self.column_order,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "assignee": self.assignee,
            "tags": [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags else [],
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
