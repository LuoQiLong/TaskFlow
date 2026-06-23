from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from ..database import get_db
from ..models.task import Task
from ..models.user import User
from ..middleware.auth import get_current_user, resolve_target_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def get_overview(
    target_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    eff_user = resolve_target_user(current_user, target_user_id)
    query = db.query(Task).filter(Task.status != "archived")
    if eff_user is not None:
        query = query.filter(Task.user_id == eff_user)
    tasks = query.all()

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
    target_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return daily task creation counts for the last N days, zero-filling gaps."""
    cutoff_date = datetime.now() - timedelta(days=days)
    eff_user = resolve_target_user(current_user, target_user_id)

    query = db.query(
        cast(Task.created_at, Date).label("date"),
        func.count(Task.id).label("count"),
    ).filter(Task.created_at >= cutoff_date, Task.status != "archived")
    if eff_user is not None:
        query = query.filter(Task.user_id == eff_user)

    results = query.group_by(cast(Task.created_at, Date)).order_by("date").all()

    # Build a lookup from date string -> count
    count_map = {}
    for r in results:
        key = r.date if isinstance(r.date, str) else r.date.isoformat()
        count_map[key] = r.count

    # Zero-fill all days in the range
    trend = []
    for i in range(days):
        d = (datetime.now() - timedelta(days=days - 1 - i)).date()
        date_str = d.isoformat()
        trend.append({"date": date_str, "count": count_map.get(date_str, 0)})

    return trend
