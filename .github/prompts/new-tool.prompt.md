---
description: Propose and build a new workbench tool with the tool-builder skill
agent: Developer
argument-hint: What should the tool do?
---

Use the tool-builder skill for the need the user described after this command (if none, ask what keeps repeating or must be exact).

1. Say whether a tool is worth it, and why.
2. If it is, propose the name, inputs, outputs, side effects, risks and tests, and wait for approval.
3. After approval: tests first, then the service, the adapter and the catalogue entry; run `python scripts/wb.py info <tool>`, a real call, and `python scripts/check_workbench.py`; then document it in the team instructions.
