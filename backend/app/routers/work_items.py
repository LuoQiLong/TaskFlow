from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.work import WorkItem, WorkLog
from ..models.user import User
from ..schemas.work import WorkItemCreate, WorkItemUpdate, WorkItemStatusUpdate, WorkItemResponse
from ..middleware.auth import get_current_user
from datetime import date, datetime

router = APIRouter(prefix="/api/work-items", tags=["work-items"])


def _get_user_work_item(item_id: int, user_id: int, db: Session) -> WorkItem:
    item = db.query(WorkItem).filter(WorkItem.id == item_id, WorkItem.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Work item not found")
    return item


def _renumber_column_orders(db: Session, user_id: int, status_filter: str):
    items = (
        db.query(WorkItem)
        .filter(WorkItem.user_id == user_id, WorkItem.status == status_filter)
        .order_by(WorkItem.column_order, WorkItem.id)
        .all()
    )
    for i, item in enumerate(items):
        item.column_order = i


@router.get("", response_model=list[WorkItemResponse])
def list_work_items(
    project_id: int | None = None,
    type: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    week_start: str | None = None,
    week_start_from: str | None = None,
    week_start_to: str | None = None,
    tag: str | None = None,
    priority: str | None = None,
    overdue: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime
    query = db.query(WorkItem).filter(WorkItem.user_id == current_user.id)

    if project_id:
        query = query.filter(WorkItem.project_id == project_id)
    if type:
        query = query.filter(WorkItem.type == type)
    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",") if s.strip()]
        if statuses:
            query = query.filter(WorkItem.status.in_(statuses))
    if tag:
        query = query.filter(WorkItem.tags.contains(tag))
    if priority:
        query = query.filter(WorkItem.priority == priority)
    if week_start:
        query = query.filter(WorkItem.week_start == week_start)
    elif week_start_from and week_start_to:
        query = query.filter(WorkItem.week_start >= week_start_from, WorkItem.week_start <= week_start_to)
    if overdue:
        query = query.filter(
            WorkItem.end_date != None,
            WorkItem.end_date < datetime.now(),
            WorkItem.status != "done",
        )

    items = query.order_by(WorkItem.project_id, WorkItem.column_order).all()
    return [WorkItemResponse.model_validate(i.to_dict()) for i in items]


@router.post("", response_model=WorkItemResponse, status_code=status.HTTP_201_CREATED)
def create_work_item(
    data: WorkItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    max_order = (
        db.query(WorkItem.column_order)
        .filter(WorkItem.user_id == current_user.id, WorkItem.status == "todo")
        .order_by(WorkItem.column_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

    item = WorkItem(
        project_id=data.project_id,
        type=data.type,
        title=data.title,
        description=data.description,
        priority=data.priority,
        estimated_hours=data.estimated_hours,
        week_start=data.week_start,
        is_cross_week=data.is_cross_week,
        tags=",".join(data.tags) if data.tags else None,
        start_date=data.start_date,
        end_date=data.end_date,
        due_date=data.due_date,
        user_id=current_user.id,
        status="todo",
        column_order=next_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return WorkItemResponse.model_validate(item.to_dict())


@router.get("/{item_id}", response_model=WorkItemResponse)
def get_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_user_work_item(item_id, current_user.id, db)
    return WorkItemResponse.model_validate(item.to_dict())


@router.put("/{item_id}", response_model=WorkItemResponse)
def update_work_item(
    item_id: int,
    data: WorkItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_user_work_item(item_id, current_user.id, db)
    update_data = data.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = ",".join(update_data["tags"]) if update_data["tags"] else None
    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return WorkItemResponse.model_validate(item.to_dict())


@router.delete("/{item_id}")
def delete_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_user_work_item(item_id, current_user.id, db)
    old_status = item.status
    db.delete(item)
    db.commit()
    _renumber_column_orders(db, current_user.id, old_status)
    db.commit()
    return {"ok": True}


@router.patch("/{item_id}/status", response_model=WorkItemResponse)
def update_work_item_status(
    item_id: int,
    data: WorkItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_user_work_item(item_id, current_user.id, db)
    old_status = item.status
    new_status = data.status

    if old_status != new_status:
        db.query(WorkItem).filter(
            WorkItem.user_id == current_user.id,
            WorkItem.status == old_status,
            WorkItem.column_order > item.column_order,
            WorkItem.id != item_id,
        ).update({WorkItem.column_order: WorkItem.column_order - 1}, synchronize_session="fetch")

        db.query(WorkItem).filter(
            WorkItem.user_id == current_user.id,
            WorkItem.status == new_status,
            WorkItem.column_order >= data.column_order,
            WorkItem.id != item_id,
        ).update({WorkItem.column_order: WorkItem.column_order + 1}, synchronize_session="fetch")
    else:
        if data.column_order > item.column_order:
            db.query(WorkItem).filter(
                WorkItem.user_id == current_user.id,
                WorkItem.status == old_status,
                WorkItem.column_order > item.column_order,
                WorkItem.column_order <= data.column_order,
                WorkItem.id != item_id,
            ).update({WorkItem.column_order: WorkItem.column_order - 1}, synchronize_session="fetch")
        elif data.column_order < item.column_order:
            db.query(WorkItem).filter(
                WorkItem.user_id == current_user.id,
                WorkItem.status == old_status,
                WorkItem.column_order >= data.column_order,
                WorkItem.column_order < item.column_order,
                WorkItem.id != item_id,
            ).update({WorkItem.column_order: WorkItem.column_order + 1}, synchronize_session="fetch")

    item.status = new_status
    item.column_order = data.column_order

    # Auto-create system work log + locked milestone when moved to "done"
    if new_status == "done" and old_status != "done":
        if item.estimated_hours and item.estimated_hours > 0:
            from ..models.work import Milestone
            # Calculate total completed milestone hours for this item
            completed_ms_hours = (
                db.query(func.coalesce(func.sum(Milestone.hours), 0))
                .filter(
                    Milestone.work_item_id == item.id,
                    Milestone.is_completed == True,
                )
                .scalar()
            ) or 0.0
            remaining = item.estimated_hours - float(completed_ms_hours)
            if remaining > 0:
                # Create work log for remaining hours
                sys_log = WorkLog(
                    work_item_id=item.id,
                    week_start=item.week_start,
                    hours=remaining,
                    log_date=date.today(),
                    note="已完成",
                    is_system=True,
                    user_id=current_user.id,
                )
                db.add(sys_log)
                # Create locked milestone (auto-completed) for remaining hours
                max_order = db.query(Milestone.sort_order).filter(
                    Milestone.work_item_id == item.id
                ).order_by(Milestone.sort_order.desc()).first()
                next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0
                ms = Milestone(
                    work_item_id=item.id,
                    title=f"完成「{item.title}」",
                    hours=remaining,
                    target_date=date.today(),
                    is_completed=True,
                    completed_at=datetime.now(),
                    is_locked=True,
                    sort_order=next_order,
                    user_id=current_user.id,
                )
                db.add(ms)
                db.flush()
                # Link work log to milestone
                sys_log.milestone_id = ms.id

    # Auto-delete system work log + locked milestones when moved out of "done"
    if old_status == "done" and new_status != "done":
        from ..models.work import Milestone
        # Delete locked milestones (their cascade will handle work logs)
        db.query(Milestone).filter(
            Milestone.work_item_id == item.id,
            Milestone.is_locked == True,
        ).delete()
        # Also delete non-milestone system logs
        db.query(WorkLog).filter(
            WorkLog.work_item_id == item.id,
            WorkLog.is_system == True,
            WorkLog.milestone_id == None,
        ).delete()

    db.commit()
    db.refresh(item)
    return WorkItemResponse.model_validate(item.to_dict())
