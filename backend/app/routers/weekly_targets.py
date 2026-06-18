from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.work import WeeklyTarget
from ..models.user import User
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/weekly-targets", tags=["weekly-targets"])


@router.get("")
def get_weekly_target(
    week_start: str = Query(description="Monday of the week, YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = (
        db.query(WeeklyTarget)
        .filter(
            WeeklyTarget.user_id == current_user.id,
            WeeklyTarget.week_start == date.fromisoformat(week_start),
        )
        .first()
    )
    if target:
        return {"week_start": week_start, "target_hours": target.target_hours, "is_custom": True}
    return {"week_start": week_start, "target_hours": 40.0, "is_custom": False}


@router.put("")
def set_weekly_target(
    week_start: str = Query(description="Monday of the week, YYYY-MM-DD"),
    target_hours: float = Query(gt=0, le=168, description="Target hours, 1-168"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = date.fromisoformat(week_start)
    target = (
        db.query(WeeklyTarget)
        .filter(
            WeeklyTarget.user_id == current_user.id,
            WeeklyTarget.week_start == ws,
        )
        .first()
    )
    if target:
        target.target_hours = target_hours
    else:
        target = WeeklyTarget(week_start=ws, target_hours=target_hours, user_id=current_user.id)
        db.add(target)
    db.commit()
    return {"week_start": week_start, "target_hours": target_hours, "is_custom": True}
