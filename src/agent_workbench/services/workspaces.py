"""Independent repository/branch work areas with a small local registry.

There is no global "active branch". Listing and registering never fetch, check out
or build anything. Creating a work area uses a Git worktree, so the main clone is
never switched. Each work area has its own JSON record, so two jobs never overwrite
one shared list. The record also holds the pipeline status (draft -> ... -> done).
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Callable

from agent_workbench.infrastructure.files import atomic_write
from agent_workbench.infrastructure.paths import ROOT_DIR
from agent_workbench.infrastructure.settings import get_setting

WORKFLOWS = {"source", "docs", "research"}
STATUSES = ("draft", "ready-for-dev", "in-dev", "ready-for-test", "changes-requested", "ready-for-acceptance",
            "accepted", "published", "done", "blocked")
ROLES = {"pm": "ProductManager", "dev": "Developer", "test": "Tester", "user": "User"}
ARTIFACT_FOLDERS = ("research", "test-results", "screenshots")
_context: ContextVar[dict | None] = ContextVar("workbench_workspace", default=None)


def _git(path: Path, *args: str) -> str:
    slow = args and args[0] in {"clone", "worktree", "read-tree", "sparse-checkout"}
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True,
                            timeout=1800 if slow else 180,
                            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_PAGER": "cat"})
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip()[:3000])
    return result.stdout.strip()


def _config_path(root: Path) -> Path:
    return root / "config" / "repositories.json"


def _load_config(root: Path = ROOT_DIR) -> dict:
    path = _config_path(root)
    if not path.is_file():
        return {"version": 1, "repositories": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _profiles(root: Path = ROOT_DIR) -> dict:
    return _load_config(root)["repositories"]


def canonical_repo(name: str, root: Path = ROOT_DIR) -> str:
    value = name.strip().casefold()
    for canonical, profile in _profiles(root).items():
        if value in {canonical.casefold(), *(alias.casefold() for alias in profile.get("aliases", []))}:
            return canonical
    raise ValueError(f"Unknown repository: {name}. Add it first with: work add-repo")


def path_setting(name: str) -> str:
    return "REPO_PATH_" + re.sub(r"[^A-Za-z0-9]+", "_", name).upper().strip("_")


def repository(name: str, root: Path = ROOT_DIR) -> dict:
    canonical = canonical_repo(name, root)
    profile = dict(_profiles(root)[canonical], name=canonical)
    raw = get_setting(path_setting(canonical), root=root) or profile.get("path") or f"../{canonical}"
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = root / path
    profile["path"] = str(path.resolve())
    profile["present"] = path.is_dir()
    profile["path_setting"] = path_setting(canonical)
    return profile


def repositories(root: Path = ROOT_DIR) -> list[dict]:
    return [repository(name, root) for name in _profiles(root)]


def add_repository(name: str, path: str = "", *, remote: str = "", default_branch: str = "main",
                   aliases: list[str] | None = None, role: str = "", workflow: str = "source",
                   init: bool = False, clone: bool = False, root: Path = ROOT_DIR,
                   runner: Callable = _git) -> dict:
    """Add a repository profile; optionally create (init) or clone the repository first."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name or ""):
        raise ValueError("Use a repository name made of letters, digits, '.', '_' or '-'.")
    if workflow not in WORKFLOWS:
        raise ValueError(f"Workflow must be one of: {', '.join(sorted(WORKFLOWS))}.")
    if init and clone:
        raise ValueError("Choose --init (new empty repository) or --clone (copy of a remote), not both.")
    config = _load_config(root)
    taken = {key.casefold() for key in config["repositories"]}
    for profile in config["repositories"].values():
        taken.update(alias.casefold() for alias in profile.get("aliases", []))
    names = {name.casefold(), *(alias.casefold() for alias in aliases or [])}
    if names & taken:
        raise ValueError(f"Name or alias already used: {', '.join(sorted(names & taken))}")
    stored = path or f"../{name}"
    location = Path(stored).expanduser()
    if not location.is_absolute():
        location = root / location
    location = location.resolve()
    if clone:
        if not remote:
            raise ValueError("--clone needs --remote <git URL>.")
        if location.exists():
            raise ValueError(f"Clone destination already exists: {location}")
        location.parent.mkdir(parents=True, exist_ok=True)
        runner(location.parent, "clone", remote, str(location))
    if init:
        if (location / ".git").exists():
            raise ValueError(f"A Git repository already exists at {location}; add it without --init.")
        location.mkdir(parents=True, exist_ok=True)
        runner(location, "init", "-b", default_branch)
        try:
            runner(location, "commit", "--allow-empty", "-m", "Initial commit")
        except RuntimeError as error:
            raise RuntimeError(f"{error}\nSet your Git identity once: git config --global user.name \"Your Name\" "
                               "and git config --global user.email you@example.com, then run add-repo again "
                               "without --init (the repository folder now exists).") from error
    config["repositories"][name] = {
        "aliases": sorted(set(aliases or [])), "remote": remote, "default_branch": default_branch,
        "path": stored, "workflow": workflow, "role": role,
    }
    path_file = _config_path(root)
    path_file.parent.mkdir(parents=True, exist_ok=True)
    path_file.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return repository(name, root)


def branch_id(branch: str) -> str:
    if not branch or branch.startswith("-") or any(ord(char) < 32 for char in branch):
        raise ValueError("A nonempty branch name without control characters is required.")
    readable = re.sub(r"[^A-Za-z0-9_-]+", "-", branch).strip("-_ ")[:60] or "branch"
    return readable + "-" + hashlib.sha256(branch.encode("utf-8")).hexdigest()[:10]


def workspace_id(repo: str, branch: str, root: Path = ROOT_DIR) -> str:
    return canonical_repo(repo, root) + "/" + branch_id(branch)


def _record_path(identifier: str, root: Path = ROOT_DIR) -> Path:
    parts = identifier.split("/")
    if len(parts) != 2 or not all(re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in parts):
        raise ValueError("Invalid workspace ID; use an ID returned by: work list")
    return root / "data" / "workspaces" / parts[0] / (parts[1] + ".json")


def _save(record: dict, root: Path = ROOT_DIR, *, new: bool = False) -> None:
    path = _record_path(record["id"], root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, indent=2, ensure_ascii=True) + "\n"
    if new:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(text)
        return
    atomic_write(path, text)


def get_workspace(identifier: str, root: Path = ROOT_DIR) -> dict:
    path = _record_path(identifier, root)
    if not path.is_file():
        raise ValueError(f"Workspace not registered: {identifier}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_workspaces(repo: str | None = None, root: Path = ROOT_DIR) -> list[dict]:
    canonical = canonical_repo(repo, root) if repo else None
    records = []
    for path in sorted((root / "data" / "workspaces").glob("*/*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if canonical is None or record["repo"] == canonical:
            records.append(record)
    return records


def current_workspace() -> dict | None:
    return _context.get()


@contextmanager
def use_workspace(identifier: str, root: Path = ROOT_DIR):
    token = _context.set(get_workspace(identifier, root))
    try:
        yield current_workspace()
    finally:
        _context.reset(token)


def bind_arguments(tool_name: str, arguments: dict) -> dict:
    """Fill a tool's target from the selected work area and reject a conflicting target."""
    record = current_workspace()
    if not record:
        return dict(arguments)
    from agent_workbench.tools.registry import metadata
    parameters = metadata(tool_name)["parameters"]
    result = dict(arguments)
    if "repo" in parameters:
        if result.get("repo") and canonical_repo(result["repo"]) != record["repo"]:
            raise ValueError("Requested repository differs from the selected work area.")
        result["repo"] = record["repo"]
    if "branch" in parameters:
        if result.get("branch") and result["branch"] != record["branch"]:
            raise ValueError("Requested branch differs from the selected work area.")
        result["branch"] = record["branch"]
    if "repo_path" in parameters:
        checkout = record.get("checkout")
        if not checkout:
            raise ValueError("This work area has no registered Git checkout.")
        if result.get("repo_path") and Path(result["repo_path"]).resolve() != Path(checkout).resolve():
            raise ValueError("Git path differs from the selected work area.")
        result["repo_path"] = checkout
    if "base" in parameters and not result.get("base"):
        result["base"] = record["base"]
    return result


def register_workspace(repo: str, branch: str, area: str | Path, *, checkout: str | Path | None = None,
                       workflow: str = "source", changelog: str | Path | None = None, base: str | None = None,
                       purpose: str = "", root: Path = ROOT_DIR, source: str = "explicit") -> dict:
    """Record existing locations without changing them or assuming Git is clean."""
    repo = canonical_repo(repo, root)
    identifier = workspace_id(repo, branch, root)
    area = Path(area).resolve()
    if not area.is_dir():
        raise ValueError(f"Working area does not exist: {area}")
    if workflow not in WORKFLOWS:
        raise ValueError(f"Workflow must be one of: {', '.join(sorted(WORKFLOWS))}.")
    profile = _profiles(root)[repo]
    record = {
        "version": 2, "id": identifier, "repo": repo, "branch": branch,
        "base": base or profile.get("default_branch", "main"),
        "area": str(area), "checkout": str(Path(checkout).resolve()) if checkout else None,
        "workflow": workflow, "purpose": purpose,
        "changelog": str(Path(changelog).resolve()) if changelog else str(area / "CHANGELOG.md"),
        "artifacts": str(area / "artifacts"),
        "registered": datetime.now().isoformat(timespec="seconds"),
        "source": source, "git_verification": "not checked", "status": "draft",
    }
    path = _record_path(identifier, root)
    if path.exists():
        existing = get_workspace(identifier, root)
        if all(existing.get(key) == record.get(key) for key in ("repo", "branch", "area", "checkout")):
            return existing
        raise ValueError(f"This repository/branch is already registered elsewhere: {identifier}")
    _save(record, root, new=True)
    return record


CHANGELOG_TEMPLATE = """# {repo} / {branch}

| Field | Value |
|---|---|
| Repo | {repo} |
| Branch | {branch} |
| Base | {base} ({revision}) |
| Checkout | {checkout} |
| Workflow | {workflow} |
| Created | {created} |

## Purpose

{purpose}

## Pipeline

draft -> ready-for-dev -> in-dev -> ready-for-test -> (changes-requested -> in-dev -> ready-for-test) -> ready-for-acceptance -> accepted -> published -> done

## Log

Newest last. Each entry: role, what changed, status, why, files, validation, commit and PR.
"""


def create_workspace(repo: str, branch: str, *, base: str | None = None, workflow: str | None = None,
                     purpose: str = "", existing_branch: bool = False, sparse: list[str] | None = None,
                     root: Path = ROOT_DIR, runner: Callable = _git) -> dict:
    """Create a branch worktree. Calling this expresses the user's approval of the branch.

    Uses the given local base (fetch it first yourself). Never switches the main clone.
    If something fails half-way, inspect what exists before retrying.
    """
    profile = repository(repo, root)
    repo = profile["name"]
    workflow = workflow or profile.get("workflow", "source")
    if workflow not in WORKFLOWS:
        raise ValueError(f"Workflow must be one of: {', '.join(sorted(WORKFLOWS))}.")
    default_branch = profile.get("default_branch", "main")
    if branch in {"master", "main", default_branch}:
        raise ValueError("Use a feature branch; base branches stay read-only references.")
    identifier = workspace_id(repo, branch, root)
    if _record_path(identifier, root).exists():
        raise ValueError("This work area already exists; use: work show / work status")
    area = root / "working" / repo / branch_id(branch)
    if area.exists():
        raise ValueError(f"Working folder already exists; register or review it instead: {area}")
    clone = Path(profile["path"])
    if not clone.is_dir():
        raise ValueError(f"Clone not found at {clone}. Clone it, or fix the path with {profile['path_setting']}.")
    actual = Path(runner(clone, "rev-parse", "--show-toplevel")).resolve()
    if actual != clone.resolve():
        raise ValueError("Configured clone path is not the Git repository root.")
    status = runner(clone, "status", "--porcelain=v1", "--branch")
    if not status.startswith("## ") or "HEAD (no branch)" in status.splitlines()[0]:
        raise ValueError("Resolve the clone's detached/unknown branch before creating a worktree.")
    base = base or default_branch
    revision = runner(clone, "rev-parse", "--verify", (branch if existing_branch else base) + "^{commit}")
    area.mkdir(parents=True)
    checkout = area / "checkout"
    for folder in ARTIFACT_FOLDERS:
        (area / "artifacts" / folder).mkdir(parents=True)
    changelog = area / "CHANGELOG.md"
    changelog.write_text(CHANGELOG_TEMPLATE.format(
        repo=repo, branch=branch, base=base, revision=revision, checkout=checkout.as_posix(), workflow=workflow,
        created=datetime.now().isoformat(timespec="minutes"),
        purpose=purpose or "Write what this branch is for before changing code."), encoding="utf-8")
    try:
        no_checkout = ["--no-checkout"] if sparse else []
        if existing_branch:
            runner(clone, "worktree", "add", *no_checkout, str(checkout), branch)
        else:
            runner(clone, "worktree", "add", *no_checkout, "-b", branch, str(checkout), revision)
        if sparse:
            runner(checkout, "sparse-checkout", "set", "--cone", *sparse)
            runner(checkout, "read-tree", "-mu", "HEAD")
    except Exception as error:
        shutil.rmtree(area, ignore_errors=True)
        try:
            runner(clone, "worktree", "prune")
        except Exception:
            pass
        if not existing_branch:
            raise RuntimeError(f"{error}\nBranch {branch} may already exist; check it, then retry with "
                               "--existing-branch.") from error
        raise
    if runner(checkout, "branch", "--show-current") != branch:
        raise ValueError("Created worktree is on an unexpected branch; inspect it before continuing.")
    record = register_workspace(repo, branch, area, checkout=checkout, workflow=workflow, changelog=changelog,
                                base=base, purpose=purpose, root=root, source="created")
    record["base_revision"] = revision
    record["clone_had_local_changes"] = len(status.splitlines()) > 1
    record["git_verification"] = "worktree created; recheck before the next Git change"
    _save(record, root)
    return record


def workspace_status(identifier: str, root: Path = ROOT_DIR, runner: Callable = _git) -> dict:
    record = get_workspace(identifier, root)
    if not record.get("checkout"):
        return {"success": False, "workspace": record, "error": "No Git checkout is registered for this area."}
    output = runner(Path(record["checkout"]), "status", "--porcelain=v1", "--branch")
    lines = output.splitlines()
    header = lines[0].removeprefix("## ") if lines else ""
    actual = re.sub(r"^(No commits yet on|Initial commit on) ", "", header.split("...", 1)[0])
    matches = actual == record["branch"]
    return {"success": matches, "workspace": record, "pipeline_status": record.get("status"),
            "actual_branch": actual, "changes": lines[1:],
            "error": None if matches else "Checkout branch differs from this work area's branch."}


def record_change(identifier: str, summary: str, *, role: str = "", reason: str = "", files: list[str] | None = None,
                  validation: str = "not run", status: str = "", commit: str = "", pr: str = "",
                  root: Path = ROOT_DIR) -> dict:
    """Append a log entry to the work area's CHANGELOG and update its pipeline status."""
    if role and role not in ROLES:
        raise ValueError(f"Role must be one of: {', '.join(ROLES)}.")
    if status and status not in STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(STATUSES)}.")
    record = get_workspace(identifier, root)
    status = status or record.get("status", "draft")
    who = f"({ROLES[role]}) " if role else ""
    path = Path(record["changelog"])
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = (f"\n### [{datetime.now().isoformat(timespec='minutes')}] {who}{summary}\n"
             f"- Status: {status}\n- Why: {reason or 'Not specified'}\n"
             f"- Files: {', '.join(files or []) or 'Not specified'}\n- Validation: {validation}\n")
    if commit:
        entry += f"- Commit: {commit}\n"
    if pr:
        entry += f"- PR: {pr}\n"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(entry)
    record.update(status=status, updated=datetime.now().isoformat(timespec="seconds"))
    if role:
        record["last_role"] = ROLES[role]
    if commit:
        record["last_commit"] = commit
    if pr:
        record["pr"] = pr
    _save(record, root)
    return record
