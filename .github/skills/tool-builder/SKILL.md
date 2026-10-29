---
name: tool-builder
description: Add a new tool to this workbench as needs evolve - decide whether a tool is worth it, design it safely (plain function, clear docstring, side-effect label, no secrets), implement it as a service plus a thin adapter, register it in the catalogue, test it and document it for the agents. Use when the same manual steps keep repeating, when a task needs exact and checkable results, or when asked to "add a tool", "automate this" or "make a command for".
---

# Tool Builder

The workbench starts with a few essential tools on purpose. New tools are added when real work shows they are needed — this skill is how.

## Is a tool worth it?

Build one when at least one of these is true:

- The same manual steps have happened three or more times, or clearly will.
- The result must be exact and checkable: calculations, dates, money, parsing, file conversion, counting.
- The step is risky and should always run with the same safety checks.
- The work handles lots of data that would waste the model's context — process it in code and return a summary.

Do not build one for a one-off command, for something a single existing command already does well, or for anything that needs secrets or permissions the user has not given.

## Design rules

1. A plain Python function with keyword arguments and type hints. Its docstring is what `info` shows the agent: first line says what it does and when; then the arguments and an example.
2. Real logic in `src/agent_workbench/services/<area>.py`; a thin adapter in `src/agent_workbench/tools/<area>.py` that returns `{"success": True, ...}`.
3. Label the side effects in the catalogue: `read` (only looks), `write` (changes local files), `interactive` (needs the user). A tool that acts on the outside world (sends, deletes, pays, publishes) must refuse unless it receives an explicit `confirm=true`, and the agent asks the user before passing it.
4. Safe defaults: dry runs for bulk changes; never delete without a flag; never overwrite unless `force=true`.
5. Secrets: read them with `get_setting("NAME")` inside the function, never at import time; never return or print them; list the setting with an empty value in `.env.example`.
6. Small outputs: return summaries and file paths; write large results to files in the work area's `artifacts/`.
7. Deterministic and safe to re-run: the same input gives the same output.
8. Errors: raise `ValueError` with a message that says what to do; the registry turns it into `{"success": false, "error": ...}`.
9. Dependencies: standard library first. If a package is truly needed, import it inside the function, fail with "pip install <package>", list it under optional dependencies in `pyproject.toml`, and check its license.
10. If the tool works on a repository checkout, name the parameter `repo_path`; then `workspace_id=<id>` fills it in automatically.

## Steps

1. **Propose** to the user: name (`verb_noun` or `noun_verb`, lowercase), purpose, inputs and outputs, side effects, risks, and how you will test it. Wait for approval.
2. **Test first:** write `tests/test_<area>.py` using `temporary_root` from `tests/support.py`.
3. **Implement** the service and the adapter; add the catalogue entry to `src/agent_workbench/tools/catalogue.json`.
4. **Check:** `python scripts/wb.py info <tool>` (are the description and parameters right?), `python scripts/wb.py call <tool> ...` on a real example, then `python scripts/check_workbench.py`.
5. **Document:** add a row to the tools table in `.github/copilot-instructions.md` (Section 13), mention the tool in the skills that should use it, and update `docs/ARCHITECTURE.md` if you added a new area.
6. **Record:** a session-log entry, and a lesson if the tool replaces a manual step that went wrong before.

## Worked example: `csv_profile`

A read-only tool that gives quick facts about a CSV file — useful before any data task.

```python
# src/agent_workbench/services/csv_profile.py
"""Quick facts about a CSV file: rows, empty cells and number ranges per column."""

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path


def profile_csv(path: str, limit: int = 100000) -> dict:
    file = Path(path).expanduser()
    if not file.is_file():
        raise ValueError(f"File not found: {file}")
    with file.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = {name: {"empty": 0, "numbers": 0, "min": None, "max": None} for name in reader.fieldnames or []}
        rows = 0
        for row in reader:
            rows += 1
            if rows > limit:
                break
            for name, value in row.items():
                if name not in columns:
                    continue
                stats = columns[name]
                if not (value or "").strip():
                    stats["empty"] += 1
                    continue
                try:
                    number = Decimal(value.replace(",", ""))
                except InvalidOperation:
                    continue
                stats["numbers"] += 1
                stats["min"] = number if stats["min"] is None else min(stats["min"], number)
                stats["max"] = number if stats["max"] is None else max(stats["max"], number)
    return {"rows": min(rows, limit), "truncated": rows > limit, "columns": columns}
```

```python
# src/agent_workbench/tools/data.py
"""Data helpers."""

from agent_workbench.services.csv_profile import profile_csv


def csv_profile(path: str, limit: int = 100000) -> dict:
    """Profile a CSV file (read-only): row count and, per column, empty cells, numeric cells, minimum and maximum. limit caps the rows read."""
    return {"success": True, **profile_csv(path, limit)}
```

Catalogue entry (add inside the JSON object, with a comma before it):

```json
"csv_profile": {"module": "tools.data", "function": "csv_profile", "category": "data", "side_effects": "read"}
```

```python
# tests/test_csv_profile.py
import unittest

from support import temporary_root

from agent_workbench.services.csv_profile import profile_csv


class CsvProfileTests(unittest.TestCase):
    def test_counts_empty_cells_and_ranges(self):
        path = temporary_root(self) / "sales.csv"
        path.write_text("region,amount\nNorth,1200.50\nSouth,\nEast,300\n", encoding="utf-8")
        result = profile_csv(str(path))
        self.assertEqual(result["rows"], 3)
        self.assertEqual(result["columns"]["amount"]["empty"], 1)
        self.assertEqual(str(result["columns"]["amount"]["max"]), "1200.50")
```

Then: `python scripts/wb.py info csv_profile`, `python scripts/wb.py call csv_profile path=<some file.csv>`, `python scripts/check_workbench.py`, and a row in the tools table.

## How the PDF tools came about (the pattern to copy)

A PDF became the source of truth for a product. Asking the model to "read the PDF" lost pictures and tables and changed numbers. That was recorded as a lesson; a tool was proposed and approved; `services/pdf_pack.py` (with pdfplumber as an optional dependency), the adapter `tools/sources.py`, catalogue entries and tests with a hand-made PDF followed; and the pdf-source-of-truth skill now tells every role how to use it. A second need — checking that numbers in generated documents come from the source — became `source_check_numbers` the same way.
