"""Read-only Git helpers. Pass workspace_id=<id> and repo_path is filled in for you."""

import os
import subprocess


def _git(repo_path: str, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo_path), *args], capture_output=True, text=True, timeout=120,
                            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_PAGER": "cat"})
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip()[:2000])
    return result.stdout.strip()


def git_status(repo_path: str) -> dict:
    """Branch, upstream and changed files of a checkout (read-only)."""
    lines = _git(repo_path, "status", "--porcelain=v1", "--branch").splitlines()
    return {"success": True, "branch_line": lines[0].removeprefix("## ") if lines else "",
            "changes": lines[1:], "clean": len(lines) <= 1}


def git_log(repo_path: str, count: int = 10) -> dict:
    """Recent commits: short hash, date, author and subject (read-only)."""
    output = _git(repo_path, "log", f"-{int(count)}", "--pretty=format:%h|%ad|%an|%s", "--date=short")
    commits = [dict(zip(("hash", "date", "author", "subject"), line.split("|", 3))) for line in output.splitlines() if line]
    return {"success": True, "commits": commits}
