from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.work import WorkItem, WorkLog
from ..models.user import User
from ..schemas.work import WorkItemCreate, WorkItemUpdate, WorkItemStatusUpdate, WorkItemResponse
from ..middleware.auth import get_current_user, resolve_target_user
from datetime import date, datetime
import os, uuid, re, json

router = APIRouter(prefix="/api/work-items", tags=["work-items"])

WORK_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "work-images")
WORK_IMAGE_ALLOWED = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

WORK_ATTACH_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "work-attachments")
WORK_ATTACH_MAX_SIZE = 50 * 1024 * 1024  # 50MB per file

_IMG_RE = re.compile(r'/static/work-images/[^\s"\'<>]+')
_ATTACH_RE = re.compile(r'/static/work-attachments/[^\s"\'<>]+')


def _extract_image_paths(html: str | None) -> set[str]:
    """Extract /static/work-images/... paths from description HTML."""
    if not html:
        return set()
    return set(_IMG_RE.findall(html))


def _delete_files(paths: set[str]):
    """Delete files from disk given their /static/... URL paths."""
    backend_root = os.path.dirname(os.path.dirname(WORK_IMAGE_DIR))
    for p in paths:
        full = os.path.join(backend_root, p.lstrip("/"))
        try:
            if os.path.isfile(full):
                os.remove(full)
        except OSError:
            pass


def _extract_attach_paths(attachments_json: str | None) -> set[str]:
    """Extract /static/work-attachments/... paths from attachments JSON."""
    if not attachments_json:
        return set()
    return set(_ATTACH_RE.findall(attachments_json))


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


@router.post("/upload-image")
async def upload_work_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload an image pasted into the work-item description editor."""
    ext = os.path.splitext(file.filename or ".png")[1].lower()
    if ext not in WORK_IMAGE_ALLOWED:
        raise HTTPException(status_code=400, detail="不支持的图片格式，仅允许 png/jpg/gif/webp/bmp")
    if ext == ".jpeg":
        ext = ".jpg"

    contents = await file.read()

    os.makedirs(WORK_IMAGE_DIR, exist_ok=True)
    filename = f"{current_user.id}_{uuid.uuid4().hex[:12]}{ext}"
    filepath = os.path.join(WORK_IMAGE_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"/static/work-images/{filename}"
    return {"url": url}


@router.post("/upload-attachment")
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a file attachment."""
    original_name = file.filename or "file"
    # Keep original extension, deny dangerous ones
    ext = os.path.splitext(original_name)[1].lower()
    dangerous = {".exe", ".sh", ".bat", ".cmd", ".ps1", ".vbs", ".com", ".msi", ".dll"}
    if ext in dangerous:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    contents = await file.read()
    if len(contents) > WORK_ATTACH_MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 50MB")

    os.makedirs(WORK_ATTACH_DIR, exist_ok=True)
    safe_name = f"{current_user.id}_{uuid.uuid4().hex[:12]}{ext}"
    filepath = os.path.join(WORK_ATTACH_DIR, safe_name)
    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"/static/work-attachments/{safe_name}"
    return {"name": original_name, "url": url, "size": len(contents)}


@router.post("/images/cleanup")
def cleanup_images(
    urls: list[str],
    current_user: User = Depends(get_current_user),
):
    """Delete orphaned uploaded images/attachments by URL list."""
    paths = set()
    for u in urls:
        if u.startswith("/static/work-images/") or u.startswith("/static/work-attachments/"):
            paths.add(u)
    _delete_files(paths)
    return {"deleted": len(paths)}


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
    search: str | None = None,
    overdue: bool = False,
    target_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime
    from sqlalchemy import or_
    eff_user = resolve_target_user(current_user, target_user_id)
    query = db.query(WorkItem)
    if eff_user is not None:
        query = query.filter(WorkItem.user_id == eff_user)

    if search:
        kw = f"%{search}%"
        query = query.filter(or_(WorkItem.title.ilike(kw), WorkItem.description.ilike(kw)))
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
        # Include cross-week items that span into this week
        query = query.filter(
            (WorkItem.week_start == week_start) |
            ((WorkItem.week_start <= week_start) & (WorkItem.week_end >= week_start))
        )
    elif week_start_from and week_start_to:
        # Include items whose [week_start, week_end] overlaps [from, to]
        from datetime import date as dt_date
        try:
            _from = dt_date.fromisoformat(week_start_from)
            _to = dt_date.fromisoformat(week_start_to)
        except (ValueError, TypeError):
            _from = _to = None
        if _from and _to:
            query = query.filter(
                WorkItem.week_start <= _to,
                (WorkItem.week_end == None) | (WorkItem.week_end >= _from)
            )
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

    # Auto-compute estimated_hours from week_hours if cross-week
    wh_json = json.dumps(data.week_hours, ensure_ascii=False) if data.week_hours else None
    est = data.estimated_hours
    if data.week_hours:
        est = sum(data.week_hours.values())

    item = WorkItem(
        project_id=data.project_id,
        type=data.type,
        title=data.title,
        description=data.description,
        priority=data.priority,
        estimated_hours=est,
        week_start=data.week_start,
        is_cross_week=bool(data.week_end and data.week_end > data.week_start),
        week_end=data.week_end,
        week_hours=wh_json,
        tags=",".join(data.tags) if data.tags else None,
        attachments=json.dumps([a.model_dump() for a in data.attachments], ensure_ascii=False) if data.attachments else None,
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
    old_description = item.description
    old_attachments = item.attachments
    update_data = data.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = ",".join(update_data["tags"]) if update_data["tags"] else None
    # Serialize attachments to JSON before setting
    if "attachments" in update_data:
        update_data["attachments"] = json.dumps(update_data["attachments"], ensure_ascii=False)
    # Auto-compute estimated_hours from week_hours
    if "week_hours" in update_data:
        wh = update_data["week_hours"]
        if wh:
            update_data["estimated_hours"] = sum(wh.values())
            update_data["week_hours"] = json.dumps(wh, ensure_ascii=False)
        else:
            update_data["week_hours"] = None
    for field, value in update_data.items():
        setattr(item, field, value)
    # Delete images removed from description
    if "description" in update_data:
        old_paths = _extract_image_paths(old_description)
        new_paths = _extract_image_paths(item.description)
        _delete_files(old_paths - new_paths)
    # Delete attachments removed
    if "attachments" in update_data:
        old_apaths = _extract_attach_paths(old_attachments)
        new_apaths = _extract_attach_paths(item.attachments)
        _delete_files(old_apaths - new_apaths)
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

    # Clean up uploaded images & attachments
    _delete_files(_extract_image_paths(item.description))
    _delete_files(_extract_attach_paths(item.attachments))

    # Break FK dependency: WorkLog.milestone_id → Milestone.id
    # must be cleared before cascade deletes Milestones, or SQL Server
    # raises a foreign-key violation.
    db.query(WorkLog).filter(WorkLog.work_item_id == item_id).update(
        {WorkLog.milestone_id: None}, synchronize_session="fetch"
    )

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

    # ── Auto-create system work log + locked milestone when moved to "done" ──
    _is_cw = bool(item.week_end and item.week_hours)
    _cw_week_not_done = False
    complete_week = data.week_start or item.week_start
    if _is_cw:
        ws_key = complete_week.isoformat() if hasattr(complete_week, 'isoformat') else str(complete_week)
        _completed_list = json.loads(item.completed_weeks) if item.completed_weeks else []
        _cw_week_not_done = ws_key not in _completed_list

    # Trigger auto-complete if: status changes to done (normal), OR cross-week week completion (status already done but another week is being completed)
    if (new_status == "done" and old_status != "done") or (_is_cw and _cw_week_not_done and new_status == "done"):
        if _is_cw:
            target_hours = item.get_hours_for_week(complete_week)
            # Mark this week as completed (keep status = "done" — frontend handles per-week column placement)
            completed = json.loads(item.completed_weeks) if item.completed_weeks else []
            ws_key = complete_week.isoformat() if hasattr(complete_week, 'isoformat') else str(complete_week)
            if ws_key not in completed:
                completed.append(ws_key)
            item.completed_weeks = json.dumps(completed, ensure_ascii=False)
        else:
            target_hours = item.estimated_hours or 0

        if target_hours > 0:
            from ..models.work import Milestone
            if _is_cw:
                # Cross-week: only subtract manually-completed milestones belonging to THIS week
                completed_ms_hours = (
                    db.query(func.coalesce(func.sum(Milestone.hours), 0))
                    .filter(
                        Milestone.work_item_id == item.id,
                        Milestone.is_completed == True,
                        Milestone.is_locked == False,
                        Milestone.week_start == complete_week,
                    )
                    .scalar()
                ) or 0.0
                remaining = target_hours - float(completed_ms_hours)
            else:
                # Non-cross-week: subtract all completed milestone hours
                completed_ms_hours = (
                    db.query(func.coalesce(func.sum(Milestone.hours), 0))
                    .filter(
                        Milestone.work_item_id == item.id,
                        Milestone.is_completed == True,
                    )
                    .scalar()
                ) or 0.0
                remaining = target_hours - float(completed_ms_hours)
            if remaining > 0:
                sys_log = WorkLog(
                    work_item_id=item.id,
                    week_start=complete_week,
                    hours=remaining,
                    log_date=date.today(),
                    note="已完成",
                    is_system=True,
                    user_id=current_user.id,
                )
                db.add(sys_log)
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
                sys_log.milestone_id = ms.id

    # ── Auto-delete system work log + locked milestones when moved out of "done" ──
    if ((old_status == "done") or bool(item.completed_weeks)) and new_status != "done":
        from ..models.work import Milestone

        # For cross-week items: only undo the current week
        if item.week_end and item.week_hours:
            undo_week = data.week_start or item.week_start
            # Remove this week from completed_weeks
            completed = json.loads(item.completed_weeks) if item.completed_weeks else []
            ws_key = undo_week.isoformat() if hasattr(undo_week, 'isoformat') else str(undo_week)
            if ws_key in completed:
                completed.remove(ws_key)
            item.completed_weeks = json.dumps(completed, ensure_ascii=False) if completed else None

            # Only delete system work log linked to a LOCKED milestone for this week
            # (manual milestone system logs are preserved)
            sys_log = db.query(WorkLog).join(
                Milestone, WorkLog.milestone_id == Milestone.id
            ).filter(
                WorkLog.work_item_id == item.id,
                WorkLog.is_system == True,
                WorkLog.week_start == undo_week,
                Milestone.is_locked == True,
            ).first()
            if sys_log:
                ms_id = sys_log.milestone_id
                sys_log.milestone_id = None  # break FK before deleting milestone
                db.flush()
                db.delete(sys_log)
                db.flush()
                if ms_id:
                    db.query(Milestone).filter(Milestone.id == ms_id, Milestone.is_locked == True).delete()
        else:
            # Non-cross-week: delete all system logs + locked milestones (original behavior)
            if item.completed_weeks:
                item.completed_weeks = None
            locked_ms_ids = db.query(Milestone.id).filter(
                Milestone.work_item_id == item.id,
                Milestone.is_locked == True,
            ).all()
            locked_ms_ids = [r[0] for r in locked_ms_ids]
            if locked_ms_ids:
                db.query(WorkLog).filter(WorkLog.milestone_id.in_(locked_ms_ids)).update(
                    {WorkLog.milestone_id: None}, synchronize_session="fetch"
                )
            db.query(WorkLog).filter(
                WorkLog.work_item_id == item.id,
                WorkLog.is_system == True,
                WorkLog.milestone_id == None,
            ).delete()
            db.query(Milestone).filter(
                Milestone.work_item_id == item.id,
                Milestone.is_locked == True,
            ).delete()

    db.commit()
    db.refresh(item)
    return WorkItemResponse.model_validate(item.to_dict())
