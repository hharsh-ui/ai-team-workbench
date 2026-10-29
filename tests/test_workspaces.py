import os
import shutil
import unittest
from pathlib import Path
from unittest import mock

from support import temporary_root

from agent_workbench.services import workspaces

IDENTITY = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com"}


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        environment = mock.patch.dict(os.environ, IDENTITY)
        environment.start()
        self.addCleanup(environment.stop)
        self.root = temporary_root(self) / "workbench"
        (self.root / "config").mkdir(parents=True)
        (self.root / "config" / "repositories.json").write_text('{"version": 1, "repositories": {}}', encoding="utf-8")
        self.repo = workspaces.add_repository("app", aliases=["web"], role="Demo app", init=True, root=self.root)

    def test_add_repository_creates_and_resolves(self):
        self.assertTrue(self.repo["present"])
        self.assertEqual(Path(self.repo["path"]), (self.root.parent / "app").resolve())
        self.assertEqual(workspaces.canonical_repo("WEB", self.root), "app")
        with self.assertRaises(ValueError):
            workspaces.add_repository("App", root=self.root)

    def test_create_status_note_and_binding(self):
        record = workspaces.create_workspace("app", "feature/login", purpose="Login page", root=self.root)
        checkout, area = Path(record["checkout"]), Path(record["area"])
        self.assertTrue((checkout / ".git").exists())
        self.assertTrue(Path(record["changelog"]).is_file())
        for folder in workspaces.ARTIFACT_FOLDERS:
            self.assertTrue((area / "artifacts" / folder).is_dir(), folder)
        self.assertEqual(record["status"], "draft")
        self.assertEqual(len(record["base_revision"]), 40)
        self.assertEqual([item["id"] for item in workspaces.list_workspaces(root=self.root)], [record["id"]])
        status = workspaces.workspace_status(record["id"], self.root)
        self.assertTrue(status["success"], status)
        updated = workspaces.record_change(record["id"], "Found 2 bugs", role="test", status="changes-requested",
                                           files=["artifacts/test-results/report.md"], validation="manual", root=self.root)
        self.assertEqual(updated["status"], "changes-requested")
        self.assertEqual(updated["last_role"], "Tester")
        self.assertIn("(Tester) Found 2 bugs", Path(record["changelog"]).read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            workspaces.record_change(record["id"], "Bad", status="finished", root=self.root)
        with workspaces.use_workspace(record["id"], self.root):
            bound = workspaces.bind_arguments("git_status", {})
            self.assertEqual(Path(bound["repo_path"]), checkout)
            with self.assertRaises(ValueError):
                workspaces.bind_arguments("git_status", {"repo_path": str(self.root)})
        with self.assertRaises(ValueError):
            workspaces.create_workspace("app", "feature/login", root=self.root)

    def test_base_branches_are_refused(self):
        for branch in ("main", "master"):
            with self.assertRaises(ValueError):
                workspaces.create_workspace("app", branch, root=self.root)

    def test_branch_ids_never_collide(self):
        self.assertNotEqual(workspaces.branch_id("Feature/X"), workspaces.branch_id("feature/x"))
        self.assertNotEqual(workspaces.branch_id("a/b"), workspaces.branch_id("a-b"))

    def test_register_is_idempotent(self):
        area = self.root / "notes"
        area.mkdir()
        first = workspaces.register_workspace("app", "research/x", area, workflow="research", root=self.root)
        second = workspaces.register_workspace("app", "research/x", area, workflow="research", root=self.root)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
