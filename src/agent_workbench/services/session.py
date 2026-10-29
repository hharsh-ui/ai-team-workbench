"""Everything an agent needs at the start of a session, in one call."""

from __future__ import annotations

from pathlib import Path
import subprocess

from agent_workbench.infrastructure.paths import ROOT_DIR
from agent_workbench.infrastructure.settings import get_setting
from agent_workbench.services.lessons import count_lessons
from agent_workbench.services.session_log import recent_entries
from agent_workbench.services.workspaces import list_workspaces


def first_name(full_name: str) -> str:
    """'Jane Doe' -> 'Jane'; 'Doe, Jane' -> 'Jane'; '' -> ''."""
    full_name = full_name.strip()
    if "," in full_name:
        full_name = full_name.split(",", 1)[1].strip()
    words = full_name.split()
    return words[0] if words else ""


def _git_user_name(root: Path) -> str:
    try:
        result = subprocess.run(["git", "config", "user.name"], cwd=root, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def session_start(count: int = 3, root: Path = ROOT_DIR) -> dict:
    name, source = get_setting("USER_FIRST_NAME", root=root), "USER_FIRST_NAME in .env"
    if not name:
        name, source = first_name(_git_user_name(root)), "git config user.name"
    if not name:
        source = "unknown: ask the user once, then suggest: python scripts/wb.py set-env USER_FIRST_NAME <name>"
    open_areas = [{key: record.get(key) for key in ("id", "repo", "branch", "status", "purpose", "last_role")}
                  for record in list_workspaces(root=root) if record.get("status") != "done"]
    return {"user_first_name": name or None, "name_source": source,
            "recent_sessions": recent_entries(count, root), "open_work_areas": open_areas,
            "lessons_recorded": count_lessons(root)}
