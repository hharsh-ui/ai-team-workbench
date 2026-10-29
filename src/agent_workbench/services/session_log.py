"""docs/SESSION_LOG.md: newest entry first, one '## [YYYY-MM-DD] Title' heading per entry."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from agent_workbench.infrastructure.paths import ROOT_DIR

HEADER = "# Session Log"
ENTRY = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] (.+)$", re.M)


def log_path(root: Path = ROOT_DIR) -> Path:
    return root / "docs" / "SESSION_LOG.md"


def recent_entries(count: int = 3, root: Path = ROOT_DIR) -> list[dict]:
    path = log_path(root)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    matches = list(ENTRY.finditer(text))
    entries = []
    for index, match in enumerate(matches[:max(count, 0)]):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        entries.append({"date": match.group(1), "title": match.group(2).strip(), "text": text[match.start():end].strip()})
    return entries


def add_entry(title: str, points: list[str], date: str = "", root: Path = ROOT_DIR) -> dict:
    title = title.strip()
    points = [point.strip() for point in points if point.strip()]
    if not title or not points:
        raise ValueError("A title and at least one point are required.")
    date = date or datetime.now().strftime("%Y-%m-%d")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("Use the date format YYYY-MM-DD.")
    entry = f"## [{date}] {title}\n\n" + "\n".join(f"- {point}" for point in points) + "\n"
    path = log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.is_file() else HEADER + "\n"
    rest = text[len(HEADER):] if text.startswith(HEADER) else "\n" + text
    rest = rest.lstrip("\n")
    path.write_text(HEADER + "\n\n" + entry + ("\n" + rest if rest else ""), encoding="utf-8")
    return {"date": date, "title": title, "points": len(points), "file": str(path)}
