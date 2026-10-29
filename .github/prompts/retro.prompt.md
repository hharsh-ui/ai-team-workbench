---
description: Run a retrospective on a finished project or a painful task and turn it into lessons and proposed improvements
agent: ProductManager
argument-hint: Which work area or project?
---

Run part B of the learning-loop skill for the work area or project the user named (if none, use the most recently accepted work area from `python scripts/wb.py work list`).

Read its changelog, PRD, test reports and the session log; fill in the retrospective template; save it in the work area's `artifacts/`; record the key lessons with `lesson_add`; and propose concrete changes to skills, agents or the team instructions for the user to approve.
