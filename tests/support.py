"""Shared test helpers (not a test module itself)."""

from pathlib import Path
import os
import shutil
import stat
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def remove_tree(path: Path) -> None:
    def make_writable_and_retry(function, target, *_):
        os.chmod(target, stat.S_IWRITE)
        function(target)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=make_writable_and_retry)
    else:
        shutil.rmtree(path, onerror=make_writable_and_retry)


def temporary_root(test) -> Path:
    """A fresh folder that is removed after the test.

    tempfile.TemporaryDirectory is avoided on purpose: on Windows it restricts the
    folder's permissions so tightly that files Git creates inside it can become
    unreadable, even to the test itself.
    """
    path = Path(tempfile.gettempdir()) / ("wb-test-" + uuid.uuid4().hex)
    path.mkdir()
    test.addCleanup(remove_tree, path)
    return path.resolve()
