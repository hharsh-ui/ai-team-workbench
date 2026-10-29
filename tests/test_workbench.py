import ast
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from support import ROOT, temporary_root

from agent_workbench.cli.arguments import parse_arguments
from agent_workbench.tools.registry import SIDE_EFFECTS, call_tool, catalogue, get_tool_info, list_tools, redacted, source_functions


def run_cli(home: Path, *words: str) -> subprocess.CompletedProcess:
    environment = {**os.environ, "WORKBENCH_HOME": str(home), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "wb.py"), *words], capture_output=True,
                          text=True, encoding="utf-8", env=environment, timeout=120)


class CatalogueTests(unittest.TestCase):
    def test_every_tool_points_to_a_documented_function(self):
        for name, spec in catalogue().items():
            with self.subTest(tool=name):
                self.assertIn(spec["side_effects"], SIDE_EFFECTS)
                self.assertTrue(spec["category"])
                node = source_functions(spec["module"])[spec["function"]]
                self.assertTrue(ast.get_docstring(node), "missing docstring")

    def test_info_describes_parameters(self):
        info = get_tool_info("lesson_add")
        self.assertTrue(info["success"])
        self.assertTrue(info["parameters"]["title"]["required"])
        self.assertFalse(info["parameters"]["cause"]["required"])
        self.assertEqual(info["parameters"]["title"]["type"], "string")

    def test_listing_never_imports_tool_modules(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1]);"
                "from agent_workbench.tools.registry import list_tools; list_tools();"
                "print(sorted(m for m in sys.modules if m.startswith('agent_workbench.tools.') and m != 'agent_workbench.tools.registry'))")
        output = subprocess.run([sys.executable, "-c", code, str(ROOT / "src")], capture_output=True, text=True, check=True)
        self.assertEqual(output.stdout.strip(), "[]")

    def test_unknown_tool_and_bad_arguments_fail_cleanly(self):
        self.assertFalse(call_tool("does_not_exist", {})["success"])
        result = call_tool("lesson_search", {"unexpected": 1})
        self.assertFalse(result["success"])
        self.assertIn("Invalid arguments", result["error"])

    def test_list_filters_by_category(self):
        result = list_tools("lessons")
        self.assertEqual(result["count"], 2)
        self.assertTrue(all(tool["category"] == "lessons" for tool in result["tools"]))


class ArgumentTests(unittest.TestCase):
    def test_json_key_value_and_flags(self):
        self.assertEqual(parse_arguments(['{"a": 1}']), {"a": 1})
        self.assertEqual(parse_arguments(["title=Ship", "v1", "count=3", "draft=true"]),
                         {"title": "Ship v1", "count": 3, "draft": True})
        self.assertEqual(parse_arguments(["--title", "Write", "PRD", "--due", "+1d", "--draft"]),
                         {"title": "Write PRD", "due": "+1d", "draft": True})

    def test_rejects_stray_words(self):
        with self.assertRaises(ValueError):
            parse_arguments(["oops"])


class RedactionTests(unittest.TestCase):
    def test_secrets_are_hidden(self):
        self.assertEqual(redacted({"token": "abc"})["token"], "[redacted]")
        self.assertNotIn("hunter2", redacted("password=hunter2 next"))
        self.assertNotIn("user:pw", redacted("https://user:pw@example.com/repo.git"))


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.home = temporary_root(self)
        (self.home / "config").mkdir()
        (self.home / "config" / "repositories.json").write_text('{"version": 1, "repositories": {}}', encoding="utf-8")

    def test_list_info_and_call(self):
        listed = run_cli(self.home, "list")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(json.loads(listed.stdout)["count"], len(catalogue()))
        added = run_cli(self.home, "call", "session_log_add", "title=First", "day", "points=Did A||Did B")
        self.assertEqual(added.returncode, 0, added.stdout + added.stderr)
        text = (self.home / "docs" / "SESSION_LOG.md").read_text(encoding="utf-8")
        self.assertIn("First day", text)
        self.assertIn("- Did B", text)
        started = json.loads(run_cli(self.home, "call", "session_start").stdout)
        self.assertEqual(started["recent_sessions"][0]["title"], "First day")

    def test_failures_exit_with_one(self):
        self.assertEqual(run_cli(self.home, "call", "nope").returncode, 1)
        self.assertEqual(run_cli(self.home, "work", "show", "bad id").returncode, 1)

    def test_set_env_never_prints_the_value(self):
        result = run_cli(self.home, "set-env", "DEMO_TOKEN", "s3cret-value")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("s3cret-value", result.stdout)
        self.assertIn("DEMO_TOKEN=s3cret-value", (self.home / ".env").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
