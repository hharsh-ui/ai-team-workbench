"""Session, session-log and lessons tools."""

from agent_workbench.services import lessons, session, session_log


def _points(points) -> list[str]:
    if isinstance(points, list):
        return [str(item) for item in points]
    return str(points).split("||")


def session_start(count: int = 3) -> dict:
    """Call once at the start of every session: the user's first name, the newest session-log entries, open work areas and the number of recorded lessons."""
    return {"success": True, **session.session_start(count)}


def session_log_recent(count: int = 3) -> dict:
    """Read the newest entries of docs/SESSION_LOG.md (default 3)."""
    entries = session_log.recent_entries(count)
    return {"success": True, "count": len(entries), "entries": entries}


def session_log_add(title: str, points: str, date: str = "") -> dict:
    """Add an entry at the top of docs/SESSION_LOG.md. Separate the points with '||'."""
    return {"success": True, **session_log.add_entry(title, _points(points), date)}


def lesson_search(query: str, limit: int = 10) -> dict:
    """Search knowledge_base/lessons.md before debugging or doing something unfamiliar. Best match first: rare words and words in a lesson's title count more. Use a few distinctive words, such as the error text or the tool name."""
    results = lessons.search_lessons(query, limit=limit)
    return {"success": True, "count": len(results), "lessons": results}


def lesson_add(title: str, status: str, symptom: str, cause: str = "", fix: str = "", rule: str = "") -> dict:
    """Add a lesson at the top of knowledge_base/lessons.md. status: FIXED, WORKAROUND, RULE, NOT A BUG, OBSOLETE or OPEN. Write the rule as an instruction for next time."""
    return {"success": True, **lessons.add_lesson(title, status, symptom, cause, fix, rule)}
