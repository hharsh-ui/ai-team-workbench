"""Repository and work-area commands. There is no implicit current branch."""

import argparse

from agent_workbench.services import workspaces


def run(argv: list[str]) -> dict:
    parser = argparse.ArgumentParser(prog="wb work", description="Repositories and independent branch work areas")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("repos", help="Show the configured repositories")
    add = commands.add_parser("add-repo", help="Add a repository profile (optionally create or clone it)")
    add.add_argument("name")
    add.add_argument("--path", default="", help="Clone location; default ../<name> next to the workbench")
    add.add_argument("--remote", default="", help="Git URL, e.g. https://github.com/you/app.git")
    add.add_argument("--default-branch", default="main")
    add.add_argument("--aliases", nargs="*", default=[])
    add.add_argument("--role", default="", help="One sentence: what this repository is for")
    add.add_argument("--workflow", choices=sorted(workspaces.WORKFLOWS), default="source")
    add.add_argument("--init", action="store_true", help="Create a new empty Git repository with one initial commit")
    add.add_argument("--clone", action="store_true", help="Clone --remote into --path first")
    listing = commands.add_parser("list", help="List work areas with their pipeline status (no Git or network calls)")
    listing.add_argument("--repo")
    for name in ("show", "status"):
        item = commands.add_parser(name, help="Show the record" if name == "show" else "Compare the record with Git")
        item.add_argument("workspace_id")
    create = commands.add_parser("create", help="Create a branch worktree from a local base (fetch first yourself)")
    create.add_argument("--repo", required=True)
    create.add_argument("--branch", required=True)
    create.add_argument("--base", help="Local ref to branch from, e.g. origin/main after a fetch")
    create.add_argument("--workflow", choices=sorted(workspaces.WORKFLOWS))
    create.add_argument("--purpose", default="")
    create.add_argument("--existing-branch", action="store_true", help="Attach an existing branch instead of creating one")
    create.add_argument("--sparse", nargs="+", metavar="DIR", help="Check out only these folders (very large repositories)")
    register = commands.add_parser("register", help="Record an existing folder/checkout without touching it")
    register.add_argument("--repo", required=True)
    register.add_argument("--branch", required=True)
    register.add_argument("--area", required=True)
    register.add_argument("--checkout")
    register.add_argument("--workflow", choices=sorted(workspaces.WORKFLOWS), default="source")
    register.add_argument("--changelog")
    register.add_argument("--base")
    register.add_argument("--purpose", default="")
    note = commands.add_parser("note", help="Log what changed, by which role, and the new pipeline status")
    note.add_argument("workspace_id")
    note.add_argument("--summary", required=True)
    note.add_argument("--role", choices=sorted(workspaces.ROLES), default="")
    note.add_argument("--status", choices=workspaces.STATUSES, default="")
    note.add_argument("--reason", default="")
    note.add_argument("--files", nargs="*", default=[])
    note.add_argument("--validation", default="not run")
    note.add_argument("--commit", default="")
    note.add_argument("--pr", default="")
    values = vars(parser.parse_args(argv))
    action = values.pop("action")
    if action == "repos":
        return {"success": True, "repositories": workspaces.repositories()}
    if action == "add-repo":
        name = values.pop("name")
        return {"success": True, "repository": workspaces.add_repository(name, **values)}
    if action == "list":
        records = workspaces.list_workspaces(values["repo"])
        board = [{key: record.get(key) for key in ("id", "status", "last_role", "purpose")} for record in records]
        return {"success": True, "count": len(records), "board": board, "workspaces": records}
    if action == "show":
        return {"success": True, "workspace": workspaces.get_workspace(values["workspace_id"])}
    if action == "status":
        return workspaces.workspace_status(values["workspace_id"])
    if action == "create":
        return {"success": True, "workspace": workspaces.create_workspace(**values)}
    if action == "register":
        repo, branch, area = values.pop("repo"), values.pop("branch"), values.pop("area")
        return {"success": True, "workspace": workspaces.register_workspace(repo, branch, area, **values)}
    identifier = values.pop("workspace_id")
    return {"success": True, "workspace": workspaces.record_change(identifier, values.pop("summary"), **values)}
