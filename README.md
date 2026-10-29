# AI Product Team Workbench

A home folder for an AI product team that works in VS Code with GitHub Copilot:

- **three role agents** — ProductManager → Developer → Tester, linked by handoff buttons;
- **shared team rules** in `.github/copilot-instructions.md`, loaded in every chat;
- **skills** — playbooks for research, PRDs, design, building, testing, security, review, debugging, PDFs as source of truth, building tools, and learning;
- **memory** — a session log (`docs/SESSION_LOG.md`) and lessons learned (`knowledge_base/lessons.md`);
- **work areas** — one isolated Git worktree per repository and branch under `working/`, with `artifacts/` and a changelog that tracks the pipeline status;
- **a small command line** — `scripts/wb.py` with the essential tools, and a skill for adding more;
- **open-source add-ons** — superpowers' engineering-method skills, gstack's specialist review methods and optional gbrain memory, each pinned to an exact commit in `config/addons.json`.

## Quick start

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python scripts\wb.py diag
python scripts\check_workbench.py
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python scripts/wb.py diag
python scripts/check_workbench.py
```

Optional, for PDFs as source of truth: `pip install pdfplumber`.

Recommended, the open-source add-ons (needs access to GitHub): `python scripts/wb.py addons fetch`, then `python scripts/wb.py addons install-skills superpowers`.

Then open this folder in VS Code, open Copilot Chat in agent mode, and pick **ProductManager** to start.

## Everyday commands

```text
python scripts/wb.py call session_start                     # name, recent sessions, open work areas
python scripts/wb.py work repos                             # repositories
python scripts/wb.py work add-repo todo-app --init --role "To-do web app"
python scripts/wb.py work create --repo todo-app --branch feature/mvp --base main --purpose "MVP"
python scripts/wb.py work list                              # pipeline board
python scripts/wb.py work note <id> --role dev --status ready-for-test --summary "Handoff: R1-R3 done"
python scripts/wb.py call lesson_search query="git identity"
python scripts/wb.py call pdf_source_pack pdf_path="C:/docs/spec.pdf"
python scripts/wb.py addons list                            # add-ons: fetched, pinned, skills
python scripts/wb.py addons check-update superpowers         # what changed upstream (the pin stays)
python scripts/check_workbench.py                           # all tests
```

## Where things are

See `docs/ARCHITECTURE.md`. Secrets and personal settings go in `.env` (copy `.env.example`); it is ignored by Git and never printed.
