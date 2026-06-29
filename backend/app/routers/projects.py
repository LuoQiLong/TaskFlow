from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.work import Project
from ..models.user import User
from ..schemas.work import ProjectCreate, ProjectUpdate, ProjectResponse
from ..middleware.auth import get_current_user, resolve_target_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_user_project(project_id: int, user_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    target_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    eff_user = resolve_target_user(current_user, target_user_id)
    query = db.query(Project)
    if eff_user is not None:
        query = query.filter(Project.user_id == eff_user)
    projects = query.order_by(Project.created_at.asc()).all()
    return projects


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(
        name=data.name,
        color=data.color,
        description=data.description,
        user_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, current_user.id, db)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_user_project(project_id, current_user.id, db)

    # Break FK chain: WorkLog.milestone_id → Milestone.id before
    # cascade reaches Milestones through Project → WorkItem → Milestone.
    from ..models.work import WorkLog, WorkItem
    work_item_ids = (
        db.query(WorkItem.id)
        .filter(WorkItem.project_id == project_id)
        .all()
    )
    if work_item_ids:
        item_ids = [r[0] for r in work_item_ids]
        db.query(WorkLog).filter(WorkLog.work_item_id.in_(item_ids)).update(
            {WorkLog.milestone_id: None}, synchronize_session="fetch"
        )

    db.delete(project)
    db.commit()
    return {"ok": True}
