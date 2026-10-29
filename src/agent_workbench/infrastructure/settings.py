"""Lazy settings: the local .env file is read only when a tool asks for a value."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import re

from .paths import ROOT_DIR

SECRET_MARKERS = ("TOKEN", "KEY", "SECRET", "PASSWORD", "PAT", "AUTH")


def env_file(root: Path = ROOT_DIR) -> Path:
    return root / ".env"


@lru_cache(maxsize=None)
def _read_env(path: str) -> dict:
    values = {}
    file = Path(path)
    if not file.is_file():
        return values
    for raw in file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_setting(key: str, default: str = "", root: Path = ROOT_DIR) -> str:
    """Process environment first, then the local .env file, then the default."""
    return os.environ.get(key) or _read_env(str(env_file(root))).get(key) or default


def is_secret(key: str) -> bool:
    return any(marker in key.upper() for marker in SECRET_MARKERS)


def set_env_value(key: str, value: str, root: Path = ROOT_DIR) -> dict:
    """Create or replace KEY=value in the local .env file. The value is never echoed back."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key or ""):
        return {"success": False, "error": "Use a KEY made of letters, digits and underscores."}
    path = env_file(root)
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    replaced = False
    for index, line in enumerate(lines):
        if line.split("=", 1)[0].strip() == key:
            lines[index] = f"{key}={value}"
            replaced = True
    if not replaced:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _read_env.cache_clear()
    return {"success": True, "key": key, "action": "replaced" if replaced else "added", "file": str(path)}
