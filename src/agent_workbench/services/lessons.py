"""knowledge_base/lessons.md: the team's learning ledger for problems, mistakes and rules (newest first)."""

from __future__ import annotations

from datetime import datetime
import math
from pathlib import Path
import re

from agent_workbench.infrastructure.paths import ROOT_DIR

STATUSES = ("FIXED", "WORKAROUND", "RULE", "NOT A BUG", "OBSOLETE", "OPEN")
ENTRY = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] (.+)$", re.M)
STOP_WORDS = frozenset("a an and are as at be but by can do does for from how i in is it its my no not of on or so "
                       "that the this to was we what when where which who why will with you".split())
DEFAULT_HEADER = """# Lessons Learned

The team's learning ledger. Search it before debugging or doing anything unfamiliar; add a lesson at the top
after fixing a problem or being corrected.

Each lesson has a **Status**: FIXED (fixed and verified), WORKAROUND (cause outside our control; follow the steps),
RULE (a way of working to follow from now on), NOT A BUG, OBSOLETE, or OPEN (not solved yet).

---
"""


def ledger_path(root: Path = ROOT_DIR) -> Path:
    return root / "knowledge_base" / "lessons.md"


def add_lesson(title: str, status: str, symptom: str, cause: str = "", fix: str = "", rule: str = "",
               date: str = "", root: Path = ROOT_DIR) -> dict:
    status = status.strip().upper()
    if status not in STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(STATUSES)}.")
    if not title.strip() or not symptom.strip():
        raise ValueError("A title and a symptom are required.")
    date = date or datetime.now().strftime("%Y-%m-%d")
    lines = [f"## [{date}] {title.strip()}", "", f"- **Status:** {status}", f"- **Symptom:** {symptom.strip()}"]
    for label, value in (("Cause", cause), ("Fix", fix), ("Rule", rule)):
        if value.strip():
            lines.append(f"- **{label}:** {value.strip()}")
    entry = "\n".join(lines) + "\n"
    path = ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.is_file() else DEFAULT_HEADER
    marker = "\n---\n"
    if marker in text:
        head, _, tail = text.partition(marker)
        text = head + marker + "\n" + entry + ("\n" + tail.lstrip("\n") if tail.strip() else "")
    else:
        text = text.rstrip("\n") + "\n\n" + entry
    path.write_text(text, encoding="utf-8")
    return {"date": date, "title": title.strip(), "status": status, "file": str(path)}


def query_words(query: str) -> list[str]:
    words = []
    for word in re.findall(r"[\w.+#-]+", query.casefold()):
        word = word.strip(".-")
        if len(word) > 1 and word not in STOP_WORDS and word not in words:
            words.append(word)
    return words


def search_lessons(query: str, root: Path = ROOT_DIR, limit: int = 10) -> list[dict]:
    """Best match first. Each query word that starts a word in a lesson adds its weight, doubled when it is in the title.

    Rare words weigh more than common ones (log(1 + lessons / lessons containing the word)), so a distinctive
    word such as an error code outranks words that appear everywhere. Ties keep the ledger order (newest first).
    An empty query returns the newest lessons.
    """
    path = ledger_path(root)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    patterns = {word: re.compile(r"(?<!\w)" + re.escape(word), re.IGNORECASE) for word in query_words(query)}
    matches = list(ENTRY.finditer(text))
    entries = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.start():end].strip()
        entries.append((match, body, [word for word, pattern in patterns.items() if pattern.search(body)]))
    weights = {word: math.log(1 + len(entries) / count) for word in patterns
               if (count := sum(1 for _, _, found in entries if word in found))}
    results = []
    for match, body, matched in entries:
        if patterns and not matched:
            continue
        title = match.group(2).strip()
        status = re.search(r"\*\*Status:\*\*\s*(.+)", body)
        score = sum(weights[word] * (2 if patterns[word].search(title) else 1) for word in matched)
        results.append({"score": round(score, 2), "matched": matched, "date": match.group(1), "title": title,
                        "status": status.group(1).strip() if status else "", "text": body})
    results.sort(key=lambda result: -result["score"])
    return results[:max(1, limit)]


def count_lessons(root: Path = ROOT_DIR) -> int:
    path = ledger_path(root)
    return len(ENTRY.findall(path.read_text(encoding="utf-8"))) if path.is_file() else 0
