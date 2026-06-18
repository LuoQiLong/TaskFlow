from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database import get_db
from ..models.task import Task
from ..models.user import User
from ..schemas.task import TaskCreate, TaskUpdate, StatusUpdate, ReorderItem, TaskResponse
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Task).filter(Task.user_id == current_user.id)

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

    update_data = data.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = ",".join(update_data["tags"]) if update_data["tags"] else None
    for field, value in update_data.items():
        setattr(task, field, value)

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
