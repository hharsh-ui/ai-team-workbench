"""Safe file writing shared by the services."""

import os
from pathlib import Path
import time
import uuid


def atomic_write(path: Path, text: str) -> None:
    """Write a temporary file, then swap it in, so a reader never sees half a file.

    Windows can lock a file for a moment right after it was written (antivirus,
    search indexer), so the swap is retried a few times before giving up.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        temporary.write_text(text, encoding="utf-8")
        for attempt in range(10):
            try:
                os.replace(temporary, path)
                return
            except PermissionError:
                if attempt == 9:
                    raise
                time.sleep(0.05 * (attempt + 1))
    finally:
        temporary.unlink(missing_ok=True)
