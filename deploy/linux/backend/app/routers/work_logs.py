from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.work import WorkLog, WorkItem
from ..models.user import User
from ..schemas.work import WorkLogCreate, WorkLogUpdate, WorkLogResponse
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/work-logs", tags=["work-logs"])


@router.get("", response_model=list[WorkLogResponse])
def list_work_logs(
    work_item_id: int | None = None,
    week_start: str | None = None,
    week_start_from: str | None = None,
    week_start_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WorkLog).filter(WorkLog.user_id == current_user.id)

    if work_item_id:
        query = query.filter(WorkLog.work_item_id == work_item_id)
    if week_start:
        query = query.filter(WorkLog.week_start == week_start)
    elif week_start_from and week_start_to:
        query = query.filter(WorkLog.week_start >= week_start_from, WorkLog.week_start <= week_start_to)

    logs = query.order_by(WorkLog.log_date.desc(), WorkLog.created_at.desc()).all()
    return logs


@router.post("", response_model=WorkLogResponse, status_code=status.HTTP_201_CREATED)
def create_work_log(
    data: WorkLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify work item exists and belongs to user
    item = db.query(WorkItem).filter(
        WorkItem.id == data.work_item_id,
        WorkItem.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Work item not found")

    log = WorkLog(
        work_item_id=data.work_item_id,
        week_start=data.week_start,
        hours=data.hours,
        log_date=data.log_date,
        note=data.note,
        user_id=current_user.id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.put("/{log_id}", response_model=WorkLogResponse)
def update_work_log(
    log_id: int,
    data: WorkLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(WorkLog).filter(
        WorkLog.id == log_id,
        WorkLog.user_id == current_user.id,
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Work log not found")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(log, field, value)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{log_id}")
def delete_work_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(WorkLog).filter(
        WorkLog.id == log_id,
        WorkLog.user_id == current_user.id,
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Work log not found")
    db.delete(log)
    db.commit()
    return {"ok": True}
