"""Workbench command line. Help, list and info never import tools or read secrets.

  python scripts/wb.py list
  python scripts/wb.py info lesson_add
  python scripts/wb.py call session_start
  python scripts/wb.py work --help
  python scripts/wb.py addons list
"""

import argparse
import json
import sys

from agent_workbench.tools.registry import call_tool, get_tool_info, list_tools


def _print(result: dict) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0 if result.get("success", True) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv[:1] == ["work"]:
            from .work import run
            return _print(run(argv[1:]))
        if argv[:1] == ["addons"]:
            from .addons import run as run_addons
            return _print(run_addons(argv[1:]))
        if argv[:1] == ["call"] and len(argv) > 1 and not argv[1].startswith("-"):
            from .arguments import parse_arguments
            return _print(call_tool(argv[1], parse_arguments(argv[2:])))
    except SystemExit:
        raise
    except Exception as error:
        return _print({"success": False, "error": str(error)})
    parser = argparse.ArgumentParser(prog="wb", description="Agent workbench: tools, work areas, session log and lessons")
    commands = parser.add_subparsers(dest="command")
    listing = commands.add_parser("list", help="List the tools")
    listing.add_argument("--category")
    info = commands.add_parser("info", help="Describe one tool and its parameters")
    info.add_argument("tool_name")
    call = commands.add_parser("call", help="Run a tool: call <tool> key=value ... (or JSON, or --key value)")
    call.add_argument("tool_name")
    commands.add_parser("work", help="Repositories and branch work areas (run: work --help)")
    commands.add_parser("addons", help="Open-source add-ons: fetch, install skills, check for updates (run: addons --help)")
    commands.add_parser("diag", help="Local health check: Python, Git, folders and config (no network)")
    env = commands.add_parser("set-env", help="Set KEY=value in the local .env file")
    env.add_argument("key")
    env.add_argument("value")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            return _print(list_tools(args.category))
        if args.command == "info":
            return _print(get_tool_info(args.tool_name))
        if args.command == "call":
            return _print(call_tool(args.tool_name, {}))
        if args.command == "diag":
            from .diagnostics import run_diag
            return _print(run_diag())
        if args.command == "set-env":
            from agent_workbench.infrastructure.settings import set_env_value
            return _print(set_env_value(args.key, args.value))
    except Exception as error:
        return _print({"success": False, "error": str(error)})
    parser.print_help()
    return 0
