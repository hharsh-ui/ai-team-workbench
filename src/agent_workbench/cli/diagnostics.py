"""Local health check. No network calls and no secret values are printed."""

import importlib.util
import platform
import shutil
import subprocess
import sys

from agent_workbench.infrastructure.paths import ROOT_DIR

FOLDERS = ("config", "docs", "knowledge_base", "templates", ".github/agents", ".github/skills", ".github/prompts")
FILES = ("config/repositories.json", ".github/copilot-instructions.md", "knowledge_base/lessons.md")


def run_diag() -> dict:
    checks = {"python >= 3.11": {"ok": sys.version_info >= (3, 11), "version": platform.python_version()}}
    git = shutil.which("git")
    checks["git"] = {"ok": bool(git), "version": subprocess.run([git, "--version"], capture_output=True, text=True).stdout.strip() if git else None}
    checks["gh (optional, for pull requests)"] = {"ok": bool(shutil.which("gh")), "required": False}
    checks["pdfplumber (optional, for PDF source packs)"] = {"ok": importlib.util.find_spec("pdfplumber") is not None, "required": False}
    for folder in FOLDERS:
        checks[folder] = {"ok": (ROOT_DIR / folder).is_dir()}
    for file in FILES:
        checks[file] = {"ok": (ROOT_DIR / file).is_file()}
    checks[".env (optional)"] = {"ok": (ROOT_DIR / ".env").is_file(), "required": False}
    try:
        from agent_workbench.services.addons import status
        for addon in status(ROOT_DIR):
            checks[f"add-on {addon['name']} fetched and pinned (optional)"] = {"ok": addon["pinned"] and addon["license_ok"], "required": False}
    except (ValueError, KeyError, OSError) as error:
        checks["config/addons.json"] = {"ok": False, "error": str(error)}
    checks["bun (optional, for native gstack or gbrain installs)"] = {"ok": bool(shutil.which("bun")), "required": False}
    healthy = all(item["ok"] for item in checks.values() if item.get("required", True))
    return {"success": healthy, "root": str(ROOT_DIR), "checks": checks}
