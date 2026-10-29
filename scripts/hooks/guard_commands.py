"""PreToolUse hook: ask the user before risky terminal commands, even when tools are auto-approved.

VS Code passes the pending tool call as JSON on standard input. Only values stored under
command-like keys are checked, so editing a document that mentions these commands is not
affected. The hook never blocks on its own: it answers "ask" or stays silent, and any
error means "no opinion".
"""

import json
import re
import sys

COMMAND_KEYS = {"command", "cmd", "commandline", "command_line", "script"}
RISKY = (
    (r"\bgit\s+push\b", "pushing to a remote"),
    (r"\bgit\s+reset\s+--hard\b", "a hard reset (discards work)"),
    (r"\bgit\s+clean\s+-\w*f", "git clean (deletes untracked files)"),
    (r"\bgit\s+branch\s+-D\b", "force-deleting a branch"),
    (r"\bgit\s+(filter-branch|filter-repo)\b|\bgit\s+rebase\b", "rewriting history"),
    (r"--no-verify\b", "skipping Git hooks"),
    (r"\brm\s+-\w*r\w*f|\brm\s+-\w*f\w*r", "recursive delete"),
    (r"\bRemove-Item\b.*-Recurse", "recursive delete"),
    (r"\b(rmdir|rd)\s+/s\b|\bdel\s+/[sq]\b", "recursive delete"),
    (r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA)\b", "dropping data"),
    (r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba|z)?sh\b|\b(iwr|Invoke-WebRequest)\b[^|]*\|\s*(iex|Invoke-Expression)\b",
     "running a downloaded script"),
)


def command_texts(value, key: str = "") -> list[str]:
    if isinstance(value, dict):
        return [text for item_key, item in value.items() for text in command_texts(item, str(item_key))]
    if isinstance(value, list):
        return [text for item in value for text in command_texts(item, key)]
    if isinstance(value, str) and key.lower() in COMMAND_KEYS:
        return [value]
    return []


def decide(payload: dict) -> dict | None:
    text = "\n".join(command_texts(payload))
    for pattern, reason in RISKY:
        if re.search(pattern, text, re.IGNORECASE):
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                           "permissionDecisionReason": f"Workbench safety rule: {reason} needs your confirmation."}}
    return None


def main() -> int:
    try:
        decision = decide(json.loads(sys.stdin.read() or "{}"))
        if decision:
            print(json.dumps(decision))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
