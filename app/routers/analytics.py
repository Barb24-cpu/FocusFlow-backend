from datetime import datetime, time, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import FocusSession, Task, Project
from app.helpers import utc_now

analytics_bp = Blueprint("analytics", __name__)


def get_focus_sessions(user_id, since=None):
    # only real focus sessions count, breaks are left out
    query = FocusSession.query.filter(
        FocusSession.user_id == user_id,
        FocusSession.start_time.isnot(None),
    )
    if since is not None:
        query = query.filter(FocusSession.start_time >= since)

    sessions = query.all()
    return [s for s in sessions if (s.session_type or "focus") == "focus"]


def calculate_streaks(days_with_focus, today):
    # days_with_focus is a set of dates that have at least one focus session.
    # Returns (current streak, longest streak) in days.
    if not days_with_focus:
        return 0, 0

    longest = 0
    run = 0
    previous = None
    for day in sorted(days_with_focus):
        if previous is not None and (day - previous).days == 1:
            run += 1
        else:
            run = 1
        if run > longest:
            longest = run
        previous = day

    # the current streak counts back from today. If there is no session
    # today yet we start from yesterday so the streak is not lost.
    current = 0
    day = today if today in days_with_focus else today - timedelta(days=1)
    while day in days_with_focus:
        current += 1
        day = day - timedelta(days=1)

    return current, longest


@analytics_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_summary():
    user_id = int(get_jwt_identity())
    today = utc_now().date()
    week_start = today - timedelta(days=6)

    sessions = get_focus_sessions(user_id)

    total_minutes = 0
    today_minutes = 0
    week_minutes = 0
    sessions_today = 0
    days_with_focus = set()

    for s in sessions:
        minutes = s.duration_min or 0
        day = s.start_time.date()

        total_minutes += minutes
        days_with_focus.add(day)

        if day == today:
            today_minutes += minutes
            sessions_today += 1
        if day >= week_start:
            week_minutes += minutes

    current_streak, longest_streak = calculate_streaks(days_with_focus, today)

    # task numbers
    tasks = Task.query.filter_by(user_id=user_id).all()
    todo = len([t for t in tasks if t.status == "todo"])
    in_progress = len([t for t in tasks if t.status == "in_progress"])
    done = len([t for t in tasks if t.status == "done"])

    projects_total = Project.query.filter_by(user_id=user_id).count()

    return jsonify({
        "focus_minutes_total": total_minutes,
        "focus_minutes_today": today_minutes,
        "focus_minutes_week": week_minutes,
        "sessions_total": len(sessions),
        "sessions_today": sessions_today,
        "tasks_total": len(tasks),
        "tasks_todo": todo,
        "tasks_in_progress": in_progress,
        "tasks_completed": done,
        "projects_total": projects_total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }), 200


@analytics_bp.route("/trends", methods=["GET"])
@jwt_required()
def get_trends():
    user_id = int(get_jwt_identity())

    # /api/analytics/trends?days=30  (default 7, between 1 and 90)
    days = request.args.get("days", 7, type=int)
    if days < 1:
        days = 1
    if days > 90:
        days = 90

    today = utc_now().date()
    first_day = today - timedelta(days=days - 1)
    since = datetime.combine(first_day, time.min)

    sessions = get_focus_sessions(user_id, since)

    # one row for every day, even the days with nothing, so the chart has no gaps
    daily = {}
    for i in range(days):
        day = first_day + timedelta(days=i)
        daily[day] = {
            "date": day.isoformat(),
            "label": day.strftime("%a"),
            "focus_minutes": 0,
            "sessions": 0,
        }

    # which project does each task belong to
    tasks = Task.query.filter_by(user_id=user_id).all()
    task_project = {t.id: t.project_id for t in tasks}
    projects = Project.query.filter_by(user_id=user_id).all()
    project_names = {p.id: p.title for p in projects}

    minutes_by_project = {}

    for s in sessions:
        minutes = s.duration_min or 0
        day = s.start_time.date()

        if day in daily:
            daily[day]["focus_minutes"] += minutes
            daily[day]["sessions"] += 1

        # time per project goes: session -> task -> project
        project_id = task_project.get(s.task_id)
        minutes_by_project[project_id] = minutes_by_project.get(project_id, 0) + minutes

    by_project = []
    for project_id, minutes in minutes_by_project.items():
        by_project.append({
            "project_id": project_id,
            "name": project_names.get(project_id, "No project"),
            "focus_minutes": minutes,
        })
    by_project.sort(key=lambda row: row["focus_minutes"], reverse=True)

    return jsonify({
        "days": days,
        "daily": list(daily.values()),
        "by_project": by_project,
    }), 200
