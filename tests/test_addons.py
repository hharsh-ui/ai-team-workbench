import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid

from support import remove_tree, temporary_root

from agent_workbench.services import addons

IDENTITY = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com"}
MIT = "MIT License\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software.\n"
IMPROVED = "---\nname: alpha\ndescription: Alpha, improved\n---\n"


def git(folder, *args) -> str:
    return subprocess.run(["git", "-C", str(folder), *args], capture_output=True, text=True, check=True,
                          env={**os.environ, **IDENTITY}).stdout.strip()


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class AddonTests(unittest.TestCase):
    """A local upstream repository stands in for GitHub, so no network is needed.

    Git starts slowly on some locked-down computers, so the upstream is built once and each test
    changes it only on its own branch.
    """

    @classmethod
    def setUpClass(cls):
        cls.upstream = Path(tempfile.gettempdir()) / ("wb-test-" + uuid.uuid4().hex) / "upstream"
        cls.upstream.mkdir(parents=True)
        cls.addClassCleanup(remove_tree, cls.upstream.parent)
        (cls.upstream / "LICENSE").write_text(MIT, encoding="utf-8")
        for skill in ("alpha", "beta"):
            (cls.upstream / "skills" / skill).mkdir(parents=True)
            (cls.upstream / "skills" / skill / "SKILL.md").write_text(
                f"---\nname: {skill}\ndescription: Test skill {skill}\n---\n", encoding="utf-8")
        git(cls.upstream, "init", "--quiet", "-b", "main")
        cls.first = cls.commit("First")

    @classmethod
    def commit(cls, message: str) -> str:
        git(cls.upstream, "add", "-A")
        git(cls.upstream, "commit", "--quiet", "-m", message)
        return git(cls.upstream, "rev-parse", "HEAD")

    def change(self, branch: str, relative: str, text: str) -> str:
        git(self.upstream, "checkout", "--quiet", "-b", branch, self.first)
        (self.upstream / relative).write_text(text, encoding="utf-8")
        return self.commit(branch)

    def setUp(self):
        self.root = temporary_root(self) / "workbench"
        (self.root / "config").mkdir(parents=True)
        self.configure(self.first)

    def configure(self, commit: str) -> None:
        addon = {"url": self.upstream.as_uri(), "commit": commit, "license": "MIT", "skills": ["alpha"]}
        (self.root / "config" / "addons.json").write_text(json.dumps({"version": 1, "addons": {"demo": addon}}), encoding="utf-8")

    def test_config_is_validated(self):
        good = {"url": "https://example.com/x.git", "commit": "a" * 40, "license": "MIT", "skills": ["alpha"]}
        addons.validate("demo", good)
        for name, change in (("Demo", {}), ("demo", {"url": "http://example.com/x.git"}), ("demo", {"url": "git@example.com:x.git"}),
                             ("demo", {"commit": "main"}), ("demo", {"license": "GPL-3.0"}), ("demo", {"skills": ["../x"]}),
                             ("demo", {"skills_dir": "../skills"})):
            with self.subTest(name=name, change=change), self.assertRaises(ValueError):
                addons.validate(name, {**good, **change})

    def test_fetch_pins_the_commit_and_refuses_local_changes(self):
        folder = addons.vendor_path("demo", self.root)
        self.assertTrue(addons.fetch("demo", self.root)["changed"])
        self.assertEqual(git(folder, "rev-parse", "HEAD"), self.first)
        self.assertFalse(addons.fetch("demo", self.root)["changed"])
        second = self.change("improved", "skills/alpha/SKILL.md", IMPROVED)
        self.configure(second)
        addons.fetch("demo", self.root)
        self.assertEqual(git(folder, "rev-parse", "HEAD"), second)
        state = addons.status(self.root)[0]
        self.assertTrue(state["pinned"] and state["license_ok"])
        (folder / "skills" / "alpha" / "SKILL.md").write_text("changed", encoding="utf-8")
        with self.assertRaises(ValueError):
            addons.fetch("demo", self.root)

    def test_a_different_license_is_refused(self):
        self.configure(self.change("relicensed", "LICENSE", "All rights reserved.\n"))
        with self.assertRaises(ValueError):
            addons.fetch("demo", self.root)
        self.assertFalse(addons.status(self.root)[0]["license_ok"])
        with self.assertRaises(ValueError):
            addons.install_skills("demo", self.root)

    def test_install_skills_protects_edits_and_workbench_skills(self):
        with self.assertRaises(ValueError):
            addons.install_skills("demo", self.root)
        addons.fetch("demo", self.root)
        installed = self.root / ".agents" / "skills" / "alpha"
        self.assertEqual(addons.install_skills("demo", self.root)["installed"], ["alpha"])
        self.assertIn("Permission is hereby granted", (installed / "ADDON-LICENSE.txt").read_text(encoding="utf-8"))
        self.assertFalse((self.root / ".agents" / "skills" / "beta").exists())
        self.assertEqual(addons.status(self.root)[0]["skills"], {"alpha": "installed"})
        addons.install_skills("demo", self.root)
        (installed / "SKILL.md").write_text("my edit", encoding="utf-8")
        self.assertEqual(addons.status(self.root)[0]["skills"], {"alpha": "edited"})
        with self.assertRaises(ValueError):
            addons.install_skills("demo", self.root)
        self.assertEqual(addons.remove_skills("demo", self.root)["kept_because_edited"], ["alpha"])
        addons.install_skills("demo", self.root, force=True)
        self.assertIn("Test skill alpha", (installed / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(addons.remove_skills("demo", self.root)["removed"], ["alpha"])
        self.assertFalse(installed.exists())
        installed.mkdir(parents=True)
        with self.assertRaises(ValueError):
            addons.install_skills("demo", self.root)
        shutil.rmtree(installed)
        (self.root / ".github" / "skills" / "alpha").mkdir(parents=True)
        with self.assertRaises(ValueError):
            addons.install_skills("demo", self.root)

    def test_check_update_lists_changes_without_moving_the_pin(self):
        addons.fetch("demo", self.root)
        second = self.change("update", "skills/alpha/SKILL.md", IMPROVED)
        update = addons.check_update("demo", ref="update", root=self.root)
        self.assertEqual(update["candidate"], second)
        self.assertEqual(update["changed_in_installed_skills"], ["skills/alpha/SKILL.md"])
        self.assertFalse(update["license_changed"])
        self.assertEqual(git(addons.vendor_path("demo", self.root), "rev-parse", "HEAD"), self.first)


if __name__ == "__main__":
    unittest.main()
