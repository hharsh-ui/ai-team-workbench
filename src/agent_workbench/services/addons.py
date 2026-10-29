"""Open-source add-ons: pinned, read-only clones of other repositories, and the skills we copy from them.

config/addons.json lists each add-on with its Git URL, the exact commit everyone uses and its license.
`fetch` checks out that commit into vendor/<name>/ (ignored by Git) and never runs any of its code.
`install_skills` copies the chosen skill folders into .agents/skills/, one of the folders VS Code reads
skills from. It records a hash of every copied file, so it never overwrites a skill it did not install
or one that was edited after installing.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from agent_workbench.infrastructure.files import atomic_write
from agent_workbench.infrastructure.paths import ROOT_DIR

NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
LICENSE_TEXT = {"MIT": "Permission is hereby granted, free of charge"}
LICENSE_FILES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE")
SKILLS_DIR = Path(".agents") / "skills"
MANIFEST = ".addons-manifest.json"


def _git(folder: Path, *args: str) -> str:
    result = subprocess.run(["git", "-c", "core.longpaths=true", "-c", "advice.detachedHead=false", "-C", str(folder), *args],
                            capture_output=True, text=True, timeout=1800,
                            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_PAGER": "cat"})
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip()[:2000])
    return result.stdout.strip()


def validate(name: str, addon: dict) -> None:
    if not NAME.match(name):
        raise ValueError(f"Add-on name '{name}' must use lowercase letters, digits and hyphens.")
    if not str(addon.get("url", "")).startswith(("https://", "file://")):
        raise ValueError(f"{name}: the url must start with https:// (file:// for a local mirror).")
    if not COMMIT.match(str(addon.get("commit", ""))):
        raise ValueError(f"{name}: commit must be a full 40-character commit SHA, so everyone gets the same files.")
    if addon.get("license") not in LICENSE_TEXT:
        raise ValueError(f"{name}: license must be one of {sorted(LICENSE_TEXT)}; agree any other license with the user first.")
    if not NAME.match(str(addon.get("skills_dir", "skills")).replace("/", "-")):
        raise ValueError(f"{name}: bad skills_dir.")
    for skill in addon.get("skills", []):
        if not NAME.match(skill):
            raise ValueError(f"{name}: bad skill name '{skill}'.")


def load_addons(root: Path = ROOT_DIR) -> dict:
    path = root / "config" / "addons.json"
    addons = json.loads(path.read_text(encoding="utf-8"))["addons"] if path.is_file() else {}
    for name, addon in addons.items():
        validate(name, addon)
    return addons


def _addon(name: str, root: Path) -> dict:
    addons = load_addons(root)
    if name not in addons:
        raise ValueError(f"Unknown add-on '{name}'. Known: {', '.join(sorted(addons)) or 'none'} (config/addons.json).")
    return addons[name]


def vendor_path(name: str, root: Path = ROOT_DIR) -> Path:
    return root / "vendor" / name


def _head(folder: Path) -> str:
    """The checked-out commit; add-on clones are always on a detached commit, so .git/HEAD holds it."""
    head = folder / ".git" / "HEAD"
    value = head.read_text(encoding="utf-8").strip() if head.is_file() else ""
    return value if COMMIT.match(value) else ""


def _license_file(folder: Path) -> Path | None:
    return next((folder / name for name in LICENSE_FILES if (folder / name).is_file()), None)


def _license_ok(folder: Path, license_name: str) -> bool:
    found = _license_file(folder)
    return bool(found) and LICENSE_TEXT[license_name] in found.read_text(encoding="utf-8", errors="replace")


def fetch(name: str, root: Path = ROOT_DIR) -> dict:
    """Check out the pinned commit into vendor/<name>/ (network only when it is not there yet)."""
    addon = _addon(name, root)
    target = vendor_path(name, root)
    if (target / ".git").exists():
        if _git(target, "status", "--porcelain"):
            raise ValueError(f"{target} has local changes. Add-on folders are read-only: remove the changes or the folder.")
    else:
        if target.exists() and any(target.iterdir()):
            raise ValueError(f"{target} exists but is not a Git checkout; move it away first.")
        target.mkdir(parents=True, exist_ok=True)
        _git(target, "init", "--quiet")
    changed = _head(target) != addon["commit"]
    if changed:
        _git(target, "fetch", "--quiet", "--depth", "1", addon["url"], addon["commit"])
        _git(target, "checkout", "--quiet", "--detach", addon["commit"])
    if not _license_ok(target, addon["license"]):
        raise ValueError(f"{name}: the license at the pinned commit is not {addon['license']}. Do not use it; tell the user.")
    return {"name": name, "path": str(target), "commit": addon["commit"], "version": addon.get("version", ""),
            "changed": changed, "license": addon["license"]}


def _hash_tree(folder: Path) -> dict:
    return {path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(folder.rglob("*")) if path.is_file()}


def _manifest(root: Path) -> dict:
    path = root / SKILLS_DIR / MANIFEST
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _save_manifest(root: Path, manifest: dict) -> None:
    atomic_write(root / SKILLS_DIR / MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def install_skills(name: str, root: Path = ROOT_DIR, force: bool = False) -> dict:
    """Copy the add-on's chosen skills into .agents/skills/ with its license. force=True replaces edited copies."""
    addon = _addon(name, root)
    source_root = vendor_path(name, root)
    if _head(source_root) != addon["commit"]:
        raise ValueError(f"{name} is not fetched at its pinned commit. Run: python scripts/wb.py addons fetch {name}")
    if not _license_ok(source_root, addon["license"]):
        raise ValueError(f"{name}: the license at the pinned commit is not {addon['license']}; nothing was installed.")
    license_file = _license_file(source_root)
    manifest = _manifest(root)
    installed = []
    for skill in addon.get("skills", []):
        source = source_root / addon.get("skills_dir", "skills") / skill
        if not (source / "SKILL.md").is_file():
            raise ValueError(f"{name} has no skill '{skill}' at commit {addon['commit'][:12]}.")
        if any(path.is_symlink() for path in (source, *source.rglob("*"))):
            raise ValueError(f"{name}/{skill} contains links; copy it by hand after checking where they point.")
        if (root / ".github" / "skills" / skill).exists():
            raise ValueError(f"'{skill}' is also a workbench skill in .github/skills; two skills with one name confuse the agents.")
        target = root / SKILLS_DIR / skill
        record = manifest.get(skill)
        if target.exists():
            if not record or record["addon"] != name:
                raise ValueError(f"{target} was not installed from {name}; rename or remove it yourself.")
            if _hash_tree(target) != record["files"] and not force:
                raise ValueError(f"{target} was edited after installing. Keep your changes, or pass force=true to replace them.")
            shutil.rmtree(target)
        shutil.copytree(source, target)
        shutil.copyfile(license_file, target / "ADDON-LICENSE.txt")
        manifest[skill] = {"addon": name, "commit": addon["commit"], "files": _hash_tree(target)}
        installed.append(skill)
    _save_manifest(root, manifest)
    return {"name": name, "commit": addon["commit"], "installed": installed, "folder": str(root / SKILLS_DIR)}


def remove_skills(name: str, root: Path = ROOT_DIR, force: bool = False) -> dict:
    """Delete the skills installed from this add-on; edited copies are kept unless force=True."""
    manifest = _manifest(root)
    removed, kept = [], []
    for skill, record in sorted(manifest.items()):
        if record["addon"] != name:
            continue
        target = root / SKILLS_DIR / skill
        if target.exists() and _hash_tree(target) != record["files"] and not force:
            kept.append(skill)
            continue
        if target.exists():
            shutil.rmtree(target)
        del manifest[skill]
        removed.append(skill)
    _save_manifest(root, manifest)
    return {"name": name, "removed": removed, "kept_because_edited": kept}


def status(root: Path = ROOT_DIR) -> list[dict]:
    """Offline status of every add-on: fetched, pinned, license and installed skills."""
    manifest = _manifest(root)
    report = []
    for name, addon in load_addons(root).items():
        folder = vendor_path(name, root)
        head = _head(folder)
        skills = {}
        for skill in addon.get("skills", []):
            record, target = manifest.get(skill), root / SKILLS_DIR / skill
            if not record or record["addon"] != name or not target.exists():
                skills[skill] = "not installed"
            elif record["commit"] != addon["commit"]:
                skills[skill] = "outdated (run install-skills)"
            else:
                skills[skill] = "installed" if _hash_tree(target) == record["files"] else "edited"
        report.append({"name": name, "version": addon.get("version", ""), "purpose": addon.get("purpose", ""),
                       "default": addon.get("default", True), "fetched": bool(head), "pinned": head == addon["commit"],
                       "license_ok": bool(head) and _license_ok(folder, addon["license"]), "skills": skills})
    return report


def check_update(name: str, ref: str = "HEAD", root: Path = ROOT_DIR) -> dict:
    """Fetch the newest commit of `ref` without moving the pin, and list what changed for review."""
    addon = _addon(name, root)
    folder = vendor_path(name, root)
    if _head(folder) != addon["commit"]:
        raise ValueError(f"Fetch {name} at its pinned commit first: python scripts/wb.py addons fetch {name}")
    _git(folder, "fetch", "--quiet", "--depth", "1", addon["url"], ref)
    candidate = _git(folder, "rev-parse", "FETCH_HEAD")
    changed = _git(folder, "diff", "--name-only", addon["commit"], candidate).splitlines()
    prefixes = tuple(f"{addon.get('skills_dir', 'skills')}/{skill}/" for skill in addon.get("skills", []))
    return {"name": name, "pinned": addon["commit"], "candidate": candidate, "changed_files": len(changed),
            "changed_in_installed_skills": [path for path in changed if path.startswith(prefixes)],
            "license_changed": any(Path(path).name.upper().startswith(("LICENSE", "LICENCE")) for path in changed),
            "review": f"git -C vendor/{name} diff {addon['commit'][:12]} {candidate[:12]} -- <paths>",
            "next": "After review: set commit (and version) in config/addons.json, then run addons fetch, "
                    "install-skills and python scripts/check_workbench.py."}
