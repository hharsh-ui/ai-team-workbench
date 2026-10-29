"""One lazy tool catalogue for list, info and call.

Listing and help read the source code with `ast` and never import a tool module,
so they have no side effects. A tool module is imported only when it is called.
"""

from __future__ import annotations

import ast
from contextlib import nullcontext
from functools import lru_cache
import importlib
import inspect
import json
from pathlib import Path
import re
import time

PACKAGE = Path(__file__).resolve().parents[1]
SIDE_EFFECTS = {"read", "write", "interactive"}
SECRET_KEYS = {"authorization", "password", "token", "access_token", "api_key", "secret", "pat"}


def redacted(value):
    if isinstance(value, dict):
        return {key: "[redacted]" if str(key).lower() in SECRET_KEYS else redacted(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redacted(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"(https?://)[^/@\s]+@", r"\1[redacted]@", value)
        return re.sub(r"(?i)((?:authorization|password|token|api[_-]?key|secret)\s*[:=]\s*)[^\s,;]+", r"\1[redacted]", value)
    return value


@lru_cache(maxsize=1)
def catalogue() -> dict:
    return json.loads((Path(__file__).parent / "catalogue.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def source_functions(module: str) -> dict:
    path = PACKAGE.joinpath(*module.split(".")).with_suffix(".py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def _kind(annotation, default) -> str:
    text = ast.unparse(annotation) if annotation is not None else ""
    for word, kind in (("bool", "boolean"), ("int", "integer"), ("float", "number"),
                       ("list", "array"), ("dict", "object"), ("str", "string")):
        if re.search(r"\b" + word + r"\b", text):
            return kind
    return {bool: "boolean", int: "integer", float: "number", list: "array", dict: "object",
            str: "string"}.get(type(default), "any")


def metadata(name: str) -> dict:
    spec = catalogue()[name]
    node = source_functions(spec["module"])[spec["function"]]
    arguments = node.args.args
    defaults = [None] * (len(arguments) - len(node.args.defaults)) + list(node.args.defaults)
    parameters = {}
    for argument, default_node in zip(arguments, defaults):
        default = ast.literal_eval(default_node) if default_node is not None else None
        parameters[argument.arg] = {"type": _kind(argument.annotation, default),
                                    "required": default_node is None, "default": default}
    return {"name": name, "category": spec["category"], "description": (ast.get_docstring(node) or name).strip(),
            "side_effects": spec.get("side_effects", "read"), "parameters": parameters,
            "implementation": f"{spec['module']}:{spec['function']}", "accepts_workspace_id": True}


def list_tools(category: str | None = None) -> dict:
    tools = []
    for name in sorted(catalogue()):
        if category and catalogue()[name]["category"] != category:
            continue
        info = metadata(name)
        tools.append({key: info[key] for key in ("name", "category", "side_effects", "description")})
    return {"success": True, "count": len(tools), "tools": tools}


def get_tool_info(name: str) -> dict:
    if name not in catalogue():
        return {"success": False, "error": f"Tool '{name}' not found. Run 'list' to see the tools."}
    return {"success": True, **metadata(name)}


def call_tool(name: str, arguments: dict | None = None) -> dict:
    started = time.perf_counter()
    try:
        if name not in catalogue():
            raise ValueError(f"Tool '{name}' not found. Run 'list' to see the tools.")
        if arguments is not None and not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be an object (key/value pairs).")
        args = dict(arguments or {})
        spec = catalogue()[name]
        workspace_id = args.pop("workspace_id", None)
        if workspace_id:
            from agent_workbench.services.workspaces import use_workspace
            context = use_workspace(workspace_id)
        else:
            context = nullcontext()
        with context:
            if workspace_id:
                from agent_workbench.services.workspaces import bind_arguments
                args = bind_arguments(name, args)
            module = importlib.import_module("agent_workbench." + spec["module"])
            function = getattr(module, spec["function"])
            try:
                inspect.signature(function).bind(**args)
            except TypeError as error:
                raise ValueError(f"Invalid arguments for {name}: {error}") from error
            result = function(**args)
        if not isinstance(result, dict):
            result = {"success": True, "result": result}
        result.setdefault("success", True)
        return {**redacted(result), "tool": name, "duration_ms": round((time.perf_counter() - started) * 1000)}
    except Exception as error:
        return {"success": False, "tool": name, "error": redacted(str(error)),
                "duration_ms": round((time.perf_counter() - started) * 1000)}
