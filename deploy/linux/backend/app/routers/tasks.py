from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import os, uuid, re, json

from ..database import get_db
from ..models.task import Task
from ..models.user import User
from ..schemas.task import TaskCreate, TaskUpdate, StatusUpdate, ReorderItem, TaskResponse
from ..middleware.auth import get_current_user, resolve_target_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

TASK_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "task-images")
TASK_IMAGE_ALLOWED = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

TASK_ATTACH_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "task-attachments")
TASK_ATTACH_MAX_SIZE = 50 * 1024 * 1024  # 50MB per file

_IMG_RE = re.compile(r'/static/task-images/[^\s"\'<>]+')
_ATTACH_RE = re.compile(r'/static/task-attachments/[^\s"\'<>]+')


def _extract_image_paths(html: str | None) -> set[str]:
    if not html:
        return set()
    return set(_IMG_RE.findall(html))


def _extract_attach_paths(attachments_json: str | None) -> set[str]:
    if not attachments_json:
        return set()
    return set(_ATTACH_RE.findall(attachments_json))


def _delete_files(paths: set[str]):
    backend_root = os.path.dirname(os.path.dirname(TASK_IMAGE_DIR))
    for p in paths:
        full = os.path.join(backend_root, p.lstrip("/"))
        try:
            if os.path.isfile(full):
                os.remove(full)
        except OSError:
            pass


def _get_user_task(task_id: int, user_id: int, db: Session) -> Task:
    """Fetch a task by ID, ensuring it belongs to the current user."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _renumber_column_orders(db: Session, user_id: int, status_filter: str):
    """Re-number column_order values so they are contiguous (0,1,2...) within a status group."""
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id, Task.status == status_filter)
        .order_by(Task.column_order, Task.id)
        .all()
    )
    for i, t in enumerate(tasks):
        t.column_order = i


@router.post("/upload-image")
async def upload_task_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload an image pasted into the task description editor."""
    ext = os.path.splitext(file.filename or ".png")[1].lower()
    if ext not in TASK_IMAGE_ALLOWED:
        raise HTTPException(status_code=400, detail="不支持的图片格式，仅允许 png/jpg/gif/webp/bmp")
    if ext == ".jpeg":
        ext = ".jpg"

    contents = await file.read()

    os.makedirs(TASK_IMAGE_DIR, exist_ok=True)
    filename = f"{current_user.id}_{uuid.uuid4().hex[:12]}{ext}"
    filepath = os.path.join(TASK_IMAGE_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"/static/task-images/{filename}"
    return {"url": url}


@router.post("/upload-attachment")
async def upload_task_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a file attachment for a task."""
    original_name = file.filename or "file"
    ext = os.path.splitext(original_name)[1].lower()
    dangerous = {".exe", ".sh", ".bat", ".cmd", ".ps1", ".vbs", ".com", ".msi", ".dll"}
    if ext in dangerous:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    contents = await file.read()
    if len(contents) > TASK_ATTACH_MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 50MB")

    os.makedirs(TASK_ATTACH_DIR, exist_ok=True)
    safe_name = f"{current_user.id}_{uuid.uuid4().hex[:12]}{ext}"
    filepath = os.path.join(TASK_ATTACH_DIR, safe_name)
    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"/static/task-attachments/{safe_name}"
    return {"name": original_name, "url": url, "size": len(contents)}


@router.post("/images/cleanup")
def cleanup_task_images(
    urls: list[str],
    current_user: User = Depends(get_current_user),
):
    """Delete orphaned uploaded images/attachments by URL list."""
    paths = set()
    for u in urls:
        if u.startswith("/static/task-images/") or u.startswith("/static/task-attachments/"):
            paths.add(u)
    _delete_files(paths)
    return {"deleted": len(paths)}


@router.get("", response_model=list[TaskResponse])
def get_tasks(
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    overdue: bool = False,
    include_archived: bool = False,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    target_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    eff_user = resolve_target_user(current_user, target_user_id)
    query = db.query(Task)
    if eff_user is not None:
        query = query.filter(Task.user_id == eff_user)

    # Default: exclude archived tasks from main view
    if not include_archived:
        query = query.filter(Task.status != "archived")

    # Filter by status (comma-separated)
    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",") if s.strip()]
        if statuses:
            query = query.filter(Task.status.in_(statuses))

    # Filter by tag
    if tag:
        query = query.filter(Task.tags.contains(tag))

    # Filter by priority (comma-separated)
    if priority:
        priorities = [p.strip() for p in priority.split(",") if p.strip()]
        if priorities:
            query = query.filter(Task.priority.in_(priorities))

    # Full-text search on title and description
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term),
            )
        )

    # Date range filter
    if date_from:
        query = query.filter(Task.created_at >= date_from)
    if date_to:
        query = query.filter(Task.created_at <= date_to + "T23:59:59")

    # Overdue filter: due_date passed and not done
    if overdue:
        from datetime import datetime
        query = query.filter(
            Task.due_date != None,
            Task.due_date < datetime.now(),
            Task.status != "done",
        )

    # Sorting (validate field name to prevent SQL injection)
    allowed_sort_fields = {"created_at", "updated_at", "title", "priority", "due_date"}
    if sort_by not in allowed_sort_fields:
        sort_by = "created_at"

    sort_col = getattr(Task, sort_by)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc(), Task.column_order.asc())
    else:
        query = query.order_by(sort_col.desc(), Task.column_order.asc())

    tasks = query.all()
    return [TaskResponse.model_validate(t.to_dict()) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Auto-assign column_order: place at end of "todo" column
    max_order = (
        db.query(Task.column_order)
        .filter(Task.user_id == current_user.id, Task.status == "todo")
        .order_by(Task.column_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

    task = Task(
        title=data.title,
        description=data.description,
        priority=data.priority,
        due_date=data.due_date,
        assignee=data.assignee,
        tags=",".join(data.tags) if data.tags else None,
        attachments=json.dumps([a.model_dump() for a in data.attachments], ensure_ascii=False) if data.attachments else None,
        user_id=current_user.id,
        status="todo",
        column_order=next_order,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task.to_dict())


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_user_task(task_id, current_user.id, db)
    return TaskResponse.model_validate(task.to_dict())


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_user_task(task_id, current_user.id, db)
    old_description = task.description
    old_attachments = task.attachments

    update_data = data.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = ",".join(update_data["tags"]) if update_data["tags"] else None
    if "attachments" in update_data:
        update_data["attachments"] = json.dumps(update_data["attachments"], ensure_ascii=False)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Delete images removed from description
    if "description" in update_data:
        old_paths = _extract_image_paths(old_description)
        new_paths = _extract_image_paths(task.description)
        _delete_files(old_paths - new_paths)

    # Delete attachments removed
    if "attachments" in update_data:
        old_apaths = _extract_attach_paths(old_attachments)
        new_apaths = _extract_attach_paths(task.attachments)
        _delete_files(old_apaths - new_apaths)

    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task.to_dict())


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_user_task(task_id, current_user.id, db)
    old_status = task.status

    # Clean up uploaded images & attachments
    _delete_files(_extract_image_paths(task.description))
    _delete_files(_extract_attach_paths(task.attachments))

    db.delete(task)
    db.commit()

    # Re-number remaining tasks in the affected column
    _renumber_column_orders(db, current_user.id, old_status)
    db.commit()

    return {"ok": True}


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_user_task(task_id, current_user.id, db)
    old_status = task.status
    new_status = data.status

    # Remove from old column: shift remaining tasks down
    if old_status != new_status:
        # Shift tasks in old column that were after this task
        db.query(Task).filter(
            Task.user_id == current_user.id,
            Task.status == old_status,
            Task.column_order > task.column_order,
            Task.id != task_id,
        ).update({Task.column_order: Task.column_order - 1}, synchronize_session="fetch")

        # Make room in new column: shift tasks at or after target position
        db.query(Task).filter(
            Task.user_id == current_user.id,
            Task.status == new_status,
            Task.column_order >= data.column_order,
            Task.id != task_id,
        ).update({Task.column_order: Task.column_order + 1}, synchronize_session="fetch")

    else:
        # Same column reorder
        if data.column_order > task.column_order:
            # Moving down: shift tasks between old+1 and new down by 1
            db.query(Task).filter(
                Task.user_id == current_user.id,
                Task.status == old_status,
                Task.column_order > task.column_order,
                Task.column_order <= data.column_order,
                Task.id != task_id,
            ).update({Task.column_order: Task.column_order - 1}, synchronize_session="fetch")
        elif data.column_order < task.column_order:
            # Moving up: shift tasks between new and old-1 up by 1
            db.query(Task).filter(
                Task.user_id == current_user.id,
                Task.status == old_status,
                Task.column_order >= data.column_order,
                Task.column_order < task.column_order,
                Task.id != task_id,
            ).update({Task.column_order: Task.column_order + 1}, synchronize_session="fetch")

    # Update the moved task
    task.status = new_status
    task.column_order = data.column_order

    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task.to_dict())


@router.patch("/reorder", response_model=list[TaskResponse])
def reorder_tasks(
    items: list[ReorderItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch update column_order for a list of tasks (within same column)."""
    updated = []
    for item in items:
        task = (
            db.query(Task)
            .filter(Task.id == item.id, Task.user_id == current_user.id)
            .first()
        )
        if task:
            task.status = item.status
            task.column_order = item.column_order
            updated.append(task)

    db.commit()
    for t in updated:
        db.refresh(t)

    return [TaskResponse.model_validate(t.to_dict()) for t in updated]
