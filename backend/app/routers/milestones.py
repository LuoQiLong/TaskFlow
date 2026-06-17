from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.work import Milestone, WorkItem
from ..models.user import User
from ..schemas.work import MilestoneCreate, MilestoneUpdate, MilestoneResponse
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/milestones", tags=["milestones"])


@router.get("", response_model=list[MilestoneResponse])
def list_milestones(
    work_item_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Milestone).filter(Milestone.user_id == current_user.id)
    if work_item_id:
        query = query.filter(Milestone.work_item_id == work_item_id)
    return query.order_by(Milestone.sort_order, Milestone.id).all()


@router.post("", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
def create_milestone(
    data: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify work item ownership
    item = db.query(WorkItem).filter(WorkItem.id == data.work_item_id, WorkItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Work item not found")

    # Auto-assign sort_order at the end
    max_order = (
        db.query(Milestone.sort_order)
        .filter(Milestone.work_item_id == data.work_item_id)
        .order_by(Milestone.sort_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

    milestone = Milestone(
        work_item_id=data.work_item_id,
        title=data.title,
        description=data.description,
        hours=data.hours,
        target_date=data.target_date,
        sort_order=next_order,
        user_id=current_user.id,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


@router.put("/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(
    milestone_id: int,
    data: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.query(Milestone).filter(Milestone.id == milestone_id, Milestone.user_id == current_user.id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(m, field, value)

    # Auto-set completed_at and create/delete work log when toggling is_completed
    if "is_completed" in update_data:
        from ..models.work import WorkLog
        m.completed_at = datetime.now() if update_data["is_completed"] else None
        if update_data["is_completed"] and m.hours and m.hours > 0:
            # Create system work log
            item = db.query(WorkItem).filter(WorkItem.id == m.work_item_id).first()
            if item:
                sys_log = WorkLog(
                    work_item_id=m.work_item_id,
                    week_start=item.week_start,
                    hours=m.hours,
                    log_date=date.today(),
                    note=f"{m.title}",
                    is_system=True,
                    milestone_id=m.id,
                    user_id=current_user.id,
                )
                db.add(sys_log)
        elif not update_data["is_completed"]:
            # Delete system work log for this milestone
            db.query(WorkLog).filter(
                WorkLog.milestone_id == m.id,
                WorkLog.is_system == True,
            ).delete()

    db.commit()
    db.refresh(m)
    return m


@router.delete("/{milestone_id}")
def delete_milestone(
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.query(Milestone).filter(Milestone.id == milestone_id, Milestone.user_id == current_user.id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    # Cascade-delete associated work log
    from ..models.work import WorkLog
    db.query(WorkLog).filter(WorkLog.milestone_id == milestone_id).delete()
    db.delete(m)
    db.commit()
    return {"ok": True}


@router.patch("/reorder", response_model=list[MilestoneResponse])
def reorder_milestones(
    items: list[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch update sort_order for milestones."""
    updated = []
    for item in items:
        m = db.query(Milestone).filter(Milestone.id == item["id"], Milestone.user_id == current_user.id).first()
        if m:
            m.sort_order = item["sort_order"]
            updated.append(m)
    db.commit()
    for m in updated:
        db.refresh(m)
    return updated
