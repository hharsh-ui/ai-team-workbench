"""Open-source add-on commands: pinned read-only clones in vendor/ and their skills in .agents/skills/."""

import argparse

from agent_workbench.services import addons


def run(argv: list[str]) -> dict:
    parser = argparse.ArgumentParser(prog="wb addons", description="Open-source add-ons pinned in config/addons.json")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("list", help="Each add-on with its purpose and status (no network)")
    fetch = commands.add_parser("fetch", help="Check out the pinned commits into vendor/ (never runs their code)")
    fetch.add_argument("names", nargs="*", help="Default: every add-on marked default in config/addons.json")
    fetch.add_argument("--all", action="store_true", help="Include the optional add-ons")
    for action, text in (("install-skills", "Copy the add-on's chosen skills into .agents/skills/"),
                         ("remove-skills", "Delete the skills installed from the add-on")):
        item = commands.add_parser(action, help=text)
        item.add_argument("name")
        item.add_argument("--force", action="store_true", help="Also replace or delete copies that were edited")
    update = commands.add_parser("check-update", help="Fetch the newest upstream commit and list what changed; the pin stays")
    update.add_argument("name")
    update.add_argument("--ref", default="HEAD", help="Branch or tag to compare with (default: the upstream default branch)")
    args = parser.parse_args(argv)
    if args.action == "list":
        return {"success": True, "addons": addons.status()}
    if args.action == "fetch":
        configured = addons.load_addons()
        names = args.names or [name for name, addon in configured.items() if args.all or addon.get("default", True)]
        results = []
        for name in names:
            try:
                results.append(addons.fetch(name))
            except Exception as error:
                results.append({"name": name, "error": str(error)})
        return {"success": all("error" not in result for result in results), "fetched": results}
    if args.action == "install-skills":
        return {"success": True, **addons.install_skills(args.name, force=args.force)}
    if args.action == "remove-skills":
        return {"success": True, **addons.remove_skills(args.name, force=args.force)}
    return {"success": True, **addons.check_update(args.name, args.ref)}
