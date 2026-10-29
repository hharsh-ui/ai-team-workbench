"""Where the workbench lives. No credentials are read and no network is used."""

import os
from pathlib import Path


def workbench_root() -> Path:
    configured = os.environ.get("WORKBENCH_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    source_root = Path(__file__).resolve().parents[3]
    if (source_root / "config" / "repositories.json").is_file():
        return source_root
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "config" / "repositories.json").is_file():
            return candidate
    return source_root


ROOT_DIR = workbench_root()
