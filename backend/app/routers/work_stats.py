import calendar
from datetime import date, datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.work import WorkLog, WorkItem, Project
from ..models.user import User
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/work-stats", tags=["work-stats"])

WEEKLY_HOURS = 40


def _get_week_start(d: date) -> date:
    """Return the Monday of the week containing date d."""
    return d - timedelta(days=d.weekday())


def _get_month_week_range(year: int, month: int) -> list[date]:
    """Return all Monday week_start dates that overlap with the given month."""
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    start_ws = _get_week_start(first_day)
    end_ws = _get_week_start(last_day)
    weeks = []
    ws = start_ws
    while ws <= end_ws:
        week_end = ws + timedelta(days=6)
        if ws <= last_day and week_end >= first_day:
            weeks.append(ws)
        ws += timedelta(days=7)
    return weeks


def _build_saturation_trend(db: Session, user_id: int, weeks: int = 12, reference_date: date | None = None) -> list[dict]:
    """Return weekly saturation trend for the last N weeks. Shared helper."""
    if reference_date is None:
        reference_date = date.today()
    current_week_start = _get_week_start(reference_date)
    trend = []
    for i in range(weeks - 1, -1, -1):
        ws = current_week_start - timedelta(weeks=i)
        week_end = ws + timedelta(days=6)
        logged = (
            db.query(func.coalesce(func.sum(WorkLog.hours), 0))
            .filter(
                WorkLog.user_id == user_id,
                WorkLog.week_start >= ws,
                WorkLog.week_start <= week_end,
            )
            .scalar()
        ) or 0
        item_ids_with_logs = (
            db.query(WorkLog.work_item_id)
            .filter(WorkLog.user_id == user_id, WorkLog.week_start >= ws, WorkLog.week_start <= week_end)
            .distinct()
            .subquery()
        )
        planned = (
            db.query(func.coalesce(func.sum(WorkItem.estimated_hours), 0))
            .filter(
                WorkItem.user_id == user_id,
                WorkItem.week_start >= ws,
                WorkItem.week_start <= week_end,
                ~WorkItem.id.in_(db.query(item_ids_with_logs.c.work_item_id)),
            )
            .scalar()
        ) or 0
        total = float(logged) + float(planned)
        trend.append({
            "week_start": ws.isoformat(),
            "week_end": week_end.isoformat(),
            "total_hours": round(total, 1),
            "logged_hours": round(float(logged), 1),
            "planned_hours": round(float(planned), 1),
            "saturation_pct": round((total / WEEKLY_HOURS) * 100, 1),
        })
    return trend


@router.get("/weekly")
def get_weekly_stats(
    week_start: str = Query(description="Monday date of the week, YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return weekly saturation stats: total hours, task/work_order split, per-project breakdown."""
    ws = date.fromisoformat(week_start)
    week_end = ws + timedelta(days=6)

    # All work logs for this week (match by range, not exact Monday)
    logs = (
        db.query(WorkLog)
        .filter(
            WorkLog.user_id == current_user.id,
            WorkLog.week_start >= ws,
            WorkLog.week_start <= week_end,
        )
        .all()
    )

    total_hours = sum(log.hours for log in logs)
    saturation_pct = round((total_hours / WEEKLY_HOURS) * 100, 1) if WEEKLY_HOURS > 0 else 0

    # Split by work item type (task vs work_order)
    task_hours = 0.0
    work_order_hours = 0.0
    project_hours: dict[int, dict] = {}  # project_id -> {name, hours}

    for log in logs:
        item = db.query(WorkItem).filter(WorkItem.id == log.work_item_id).first()
        if not item:
            continue

        if item.type == "task":
            task_hours += log.hours
        else:
            work_order_hours += log.hours

        pid = item.project_id
        if pid not in project_hours:
            proj = db.query(Project).filter(Project.id == pid).first()
            project_hours[pid] = {
                "project_id": pid,
                "project_name": proj.name if proj else "Unknown",
                "project_color": proj.color if proj else "#999",
                "hours": 0.0,
            }
        project_hours[pid]["hours"] += log.hours

    return {
        "week_start": week_start,
        "week_end": week_end.isoformat(),
        "total_hours": round(total_hours, 1),
        "weekly_target": WEEKLY_HOURS,
        "saturation_pct": saturation_pct,
        "task_hours": round(task_hours, 1),
        "work_order_hours": round(work_order_hours, 1),
        "project_breakdown": sorted(project_hours.values(), key=lambda x: x["hours"], reverse=True),
        "remaining_hours": round(max(0, WEEKLY_HOURS - total_hours), 1),
    }


@router.get("/trend")
def get_trend_stats(
    weeks: int = Query(default=12, ge=1, le=52),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return weekly hour totals for the last N weeks (by week_start), zero-filled."""
    return _build_saturation_trend(db, current_user.id, weeks)


@router.get("/monthly")
def get_monthly_stats(
    year: int = Query(ge=2020, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return monthly saturation stats with weekly breakdown."""
    month_weeks = _get_month_week_range(year, month)

    # Weekly breakdown within the month
    weekly_breakdown = []
    month_total = 0.0
    month_task_hours = 0.0
    month_wo_hours = 0.0
    project_hours: dict[int, dict] = {}

    for ws in month_weeks:
        logs = (
            db.query(WorkLog)
            .filter(
                WorkLog.user_id == current_user.id,
                WorkLog.week_start == ws,
            )
            .all()
        )
        week_total = sum(log.hours for log in logs)
        month_total += week_total

        week_task = 0.0
        week_wo = 0.0
        for log in logs:
            item = db.query(WorkItem).filter(WorkItem.id == log.work_item_id).first()
            if not item:
                continue
            if item.type == "task":
                week_task += log.hours
            else:
                week_wo += log.hours

            pid = item.project_id
            if pid not in project_hours:
                proj = db.query(Project).filter(Project.id == pid).first()
                project_hours[pid] = {
                    "project_id": pid,
                    "project_name": proj.name if proj else "Unknown",
                    "project_color": proj.color if proj else "#999",
                    "hours": 0.0,
                }
            project_hours[pid]["hours"] += log.hours

        month_task_hours += week_task
        month_wo_hours += week_wo
        weekly_breakdown.append({
            "week_start": ws.isoformat(),
            "total_hours": round(week_total, 1),
            "task_hours": round(week_task, 1),
            "work_order_hours": round(week_wo, 1),
        })

    num_weeks = len(month_weeks)
    monthly_target = num_weeks * WEEKLY_HOURS

    return {
        "year": year,
        "month": month,
        "num_weeks": num_weeks,
        "monthly_target": monthly_target,
        "total_hours": round(month_total, 1),
        "saturation_pct": round((month_total / monthly_target) * 100, 1) if monthly_target > 0 else 0,
        "task_hours": round(month_task_hours, 1),
        "work_order_hours": round(month_wo_hours, 1),
        "remaining_hours": round(max(0, monthly_target - month_total), 1),
        "weekly_breakdown": weekly_breakdown,
        "project_breakdown": sorted(project_hours.values(), key=lambda x: x["hours"], reverse=True),
    }


@router.get("/dashboard")
def get_dashboard_stats(
    year: int = Query(ge=2020, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return comprehensive dashboard stats: all charts in one call."""
    month_weeks = _get_month_week_range(year, month)
    if not month_weeks:
        month_weeks = [_get_week_start(date(year, month, 1))]
    num_weeks = len(month_weeks)
    monthly_target = num_weeks * WEEKLY_HOURS
    num_days = calendar.monthrange(year, month)[1]
    first_ws = month_weeks[0]
    last_week_end = month_weeks[-1] + timedelta(days=6)

    # Fetch all logs for this month's weeks at once
    logs = (
        db.query(WorkLog)
        .filter(
            WorkLog.user_id == current_user.id,
            WorkLog.week_start >= first_ws,
            WorkLog.week_start <= last_week_end,
        )
        .all()
    )

    # Fetch all work items for the user (needed for type/tags lookup)
    item_ids = list(set(log.work_item_id for log in logs))
    items_map: dict[int, WorkItem] = {}
    if item_ids:
        items = db.query(WorkItem).filter(WorkItem.id.in_(item_ids)).all()
        items_map = {it.id: it for it in items}

    # Aggregate: project_hours, type_breakdown, tag_distribution, daily_heatmap, weekly_breakdown
    project_hours: dict[int, dict] = {}
    task_hours = 0.0
    work_order_hours = 0.0
    tag_hours: dict[str, dict] = {}  # tag -> {hours, count}
    daily_hours: dict[str, float] = {}  # "YYYY-MM-DD" -> hours
    weekly_data: dict[str, dict] = {}  # week_start -> {total, task, wo}

    for ws in month_weeks:
        ws_str = ws.isoformat()
        weekly_data[ws_str] = {"total": 0.0, "task": 0.0, "wo": 0.0}

    for log in logs:
        item = items_map.get(log.work_item_id)
        if not item:
            continue

        h = float(log.hours)

        # type breakdown
        if item.type == "task":
            task_hours += h
        else:
            work_order_hours += h

        # project hours
        pid = item.project_id
        if pid not in project_hours:
            proj = db.query(Project).filter(Project.id == pid).first()
            project_hours[pid] = {
                "project_id": pid,
                "project_name": proj.name if proj else "Unknown",
                "project_color": proj.color if proj else "#999",
                "hours": 0.0,
            }
        project_hours[pid]["hours"] += h

        # tag distribution
        if item.tags:
            for tag in item.tags.split(","):
                t = tag.strip()
                if not t:
                    continue
                if t not in tag_hours:
                    tag_hours[t] = {"tag": t, "hours": 0.0, "count": 0}
                tag_hours[t]["hours"] += h
                tag_hours[t]["count"] += 1

        # daily heatmap (use log_date if available, fall back to week_start)
        d = log.log_date if log.log_date else log.week_start
        if d:
            d_str = d.isoformat()
            daily_hours[d_str] = daily_hours.get(d_str, 0) + h

        # weekly breakdown
        ws_str = log.week_start.isoformat()
        if ws_str in weekly_data:
            weekly_data[ws_str]["total"] += h
            if item.type == "task":
                weekly_data[ws_str]["task"] += h
            else:
                weekly_data[ws_str]["wo"] += h
        else:
            # log belongs to a week outside the month range but within range query
            pass

    total_hours = task_hours + work_order_hours

    # Build daily heatmap array (zero-fill all days in month)
    daily_heatmap = []
    for d in range(1, num_days + 1):
        d_str = date(year, month, d).isoformat()
        dow = date(year, month, d).weekday()  # 0=Mon, 6=Sun
        daily_heatmap.append({
            "date": d_str,
            "hours": round(daily_hours.get(d_str, 0), 1),
            "day_of_week": dow,
        })

    # Overdue by project (scoped to selected month)
    month_start = date(year, month, 1)
    month_end = date(year, month, num_days)
    overdue_by_project: dict[int, dict] = {}
    overdue_items = (
        db.query(WorkItem)
        .filter(
            WorkItem.user_id == current_user.id,
            WorkItem.end_date.isnot(None),
            WorkItem.end_date >= month_start,
            WorkItem.end_date <= month_end,
            WorkItem.status != "done",
        )
        .all()
    )
    for oi in overdue_items:
        pid = oi.project_id
        if pid not in overdue_by_project:
            proj = db.query(Project).filter(Project.id == pid).first()
            overdue_by_project[pid] = {
                "project_id": pid,
                "project_name": proj.name if proj else "Unknown",
                "project_color": proj.color if proj else "#999",
                "overdue_count": 0,
            }
        overdue_by_project[pid]["overdue_count"] += 1

    # Trends scoped to the selected month's last week
    month_last_day = date(year, month, num_days)
    month_ref_ws = _get_week_start(month_last_day)

    # Creation trend (last 12 weeks ending at selected month's last week)
    creation_trend = []
    for i in range(11, -1, -1):
        ws = month_ref_ws - timedelta(weeks=i)
        we = ws + timedelta(days=6)
        count = (
            db.query(func.count(WorkItem.id))
            .filter(
                WorkItem.user_id == current_user.id,
                WorkItem.created_at >= ws,
                WorkItem.created_at <= we + timedelta(days=1),
            )
            .scalar()
        ) or 0
        creation_trend.append({"week_start": ws.isoformat(), "count": count})

    return {
        "period": {
            "year": year,
            "month": month,
            "num_weeks": num_weeks,
            "monthly_target": monthly_target,
        },
        "summary": {
            "total_hours": round(total_hours, 1),
            "task_hours": round(task_hours, 1),
            "work_order_hours": round(work_order_hours, 1),
            "saturation_pct": round((total_hours / monthly_target) * 100, 1) if monthly_target > 0 else 0,
            "remaining_hours": round(max(0, monthly_target - total_hours), 1),
        },
        "project_hours": sorted(project_hours.values(), key=lambda x: x["hours"], reverse=True),
        "type_breakdown": {
            "task_hours": round(task_hours, 1),
            "work_order_hours": round(work_order_hours, 1),
        },
        "daily_heatmap": daily_heatmap,
        "tag_distribution": sorted(tag_hours.values(), key=lambda x: x["hours"], reverse=True),
        "overdue_by_project": sorted(overdue_by_project.values(), key=lambda x: x["overdue_count"], reverse=True),
        "saturation_trend": _build_saturation_trend(db, current_user.id, 12, month_last_day),
        "creation_trend": creation_trend,
        "weekly_breakdown": [
            {
                "week_start": ws_str,
                "total_hours": round(wd["total"], 1),
                "task_hours": round(wd["task"], 1),
                "work_order_hours": round(wd["wo"], 1),
            }
            for ws_str, wd in weekly_data.items()
        ],
    }
