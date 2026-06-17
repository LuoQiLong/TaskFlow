from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.task import Task
from ..models.user import User
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()

    total = len(tasks)
    status_counts = {"todo": 0, "in_progress": 0, "done": 0}
    priority_counts = {"low": 0, "medium": 0, "high": 0}

    for t in tasks:
        if t.status in status_counts:
            status_counts[t.status] += 1
        if t.priority in priority_counts:
            priority_counts[t.priority] += 1

    return {
        "total": total,
        "status_counts": status_counts,
        "priority_counts": priority_counts,
    }


@router.get("/trend")
def get_trend(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return daily task creation counts for the last N days, zero-filling gaps."""
    cutoff_date = datetime.now() - timedelta(days=days)

    results = (
        db.query(
            func.date(Task.created_at).label("date"),
            func.count(Task.id).label("count"),
        )
        .filter(Task.user_id == current_user.id, Task.created_at >= cutoff_date)
        .group_by(func.date(Task.created_at))
        .order_by("date")
        .all()
    )

    # Build a lookup from date string -> count
    count_map = {r.date: r.count for r in results}

    # Zero-fill all days in the range
    trend = []
    for i in range(days):
        d = (datetime.now() - timedelta(days=days - 1 - i)).date()
        date_str = d.isoformat()
        trend.append({"date": date_str, "count": count_map.get(date_str, 0)})

    return trend
