import json
import re
import unittest

from support import ROOT

INSTRUCTIONS = ROOT / ".github" / "copilot-instructions.md"
DISCLOSURE = "I have used these skills:"
REQUIRED_HEADINGS = (
    "## 1. Who We Are",
    "## 3. How We Think",
    "## 5. Session Routine",
    "## 7. The Pipeline: Product Manager, Developer, Tester",
    "## 8. Work Areas",
    "## 10. Git Safety",
    "## 12. Security Baseline",
    "## 14. Skills",
    "## 15. Add-ons",
    "## 16. Sources of Truth",
    "## 17. Learning Loop",
    "## 19. Before Ending Every Turn",
)
BUILT_IN_AGENTS = {"ask", "agent", "plan", "edit"}
SECRET_PATTERNS = (
    r"\bghp_[A-Za-z0-9]{30,}", r"\bgithub_pat_[A-Za-z0-9_]{40,}", r"\bsk-[A-Za-z0-9]{20,}",
    r"\bPMAK-[A-Za-z0-9-]{20,}", r"\bAKIA[0-9A-Z]{16}\b", r"\bxox[abprs]-[A-Za-z0-9-]{20,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
)
SKIPPED_FOLDERS = {".git", ".venv", "venv", "data", "working", "sources", "vendor", ".agents", "__pycache__", "node_modules"}
CONFLICTING_ADDON_SKILLS = {"using-superpowers", "using-git-worktrees", "diagnosing-superpowers"}
TEXT_SUFFIXES = {".md", ".py", ".json", ".toml", ".txt", ".yml", ".yaml", ".example", ".gitignore"}


def frontmatter(text: str) -> tuple[dict, str] | None:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    block, values = text[4:end], {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#", "-")):
            key, _, value = line.partition(":")
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values, block


def workbench_files(suffixes=None):
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if path.is_file() and not set(relative.parts) & SKIPPED_FOLDERS:
            if suffixes is None or path.suffix in suffixes or path.name in suffixes:
                yield path


def agent_files() -> list:
    return sorted((ROOT / ".github" / "agents").glob("*.agent.md"))


def skill_folders() -> list:
    return sorted(path for path in (ROOT / ".github" / "skills").iterdir() if path.is_dir())


class InstructionTests(unittest.TestCase):
    def test_required_sections_and_one_disclosure_rule(self):
        text = INSTRUCTIONS.read_text(encoding="utf-8")
        for heading in REQUIRED_HEADINGS:
            self.assertIn("\n" + heading + "\n", text)
        self.assertEqual(text.count(DISCLOSURE), 1)

    def test_every_skill_and_agent_is_mentioned(self):
        text = INSTRUCTIONS.read_text(encoding="utf-8")
        for name in [folder.name for folder in skill_folders()] + [path.name.removesuffix(".agent.md") for path in agent_files()]:
            self.assertIn(name, text, f"Mention {name} in .github/copilot-instructions.md")


class AgentTests(unittest.TestCase):
    def test_agents_have_valid_frontmatter_and_handoffs(self):
        names = {path.name.removesuffix(".agent.md") for path in agent_files()}
        self.assertTrue(names)
        for path in agent_files():
            with self.subTest(agent=path.name):
                parsed = frontmatter(path.read_text(encoding="utf-8"))
                self.assertIsNotNone(parsed, "frontmatter missing")
                meta, block = parsed
                self.assertEqual(meta.get("name"), path.name.removesuffix(".agent.md"))
                self.assertTrue(meta.get("description"))
                self.assertNotIn("model", meta)
                self.assertIn("\n## How You Think\n", path.read_text(encoding="utf-8").replace("\r\n", "\n"))
                for target in re.findall(r"^\s+agent:\s*\"?([\w-]+)", block, re.M):
                    self.assertIn(target, names, f"handoff to unknown agent {target}")


class SkillTests(unittest.TestCase):
    def test_skill_frontmatter_and_size(self):
        folders = skill_folders()
        self.assertTrue(folders)
        for folder in folders:
            with self.subTest(skill=folder.name):
                self.assertRegex(folder.name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
                text = (folder / "SKILL.md").read_text(encoding="utf-8")
                parsed = frontmatter(text)
                self.assertIsNotNone(parsed, "frontmatter missing")
                meta = parsed[0]
                self.assertEqual(meta.get("name"), folder.name)
                description = meta.get("description", "")
                self.assertTrue(20 <= len(description) <= 1024)
                self.assertNotIn(": ", description)
                self.assertNotIn(DISCLOSURE, text)
                self.assertLess(len(text.splitlines()), 500)


class PromptAndHookTests(unittest.TestCase):
    def test_prompts_have_descriptions_and_known_agents(self):
        agents = {path.name.removesuffix(".agent.md") for path in agent_files()} | BUILT_IN_AGENTS
        for path in sorted((ROOT / ".github" / "prompts").glob("*.prompt.md")):
            with self.subTest(prompt=path.name):
                parsed = frontmatter(path.read_text(encoding="utf-8"))
                self.assertIsNotNone(parsed, "frontmatter missing")
                meta = parsed[0]
                self.assertTrue(meta.get("description"))
                if "agent" in meta:
                    self.assertIn(meta["agent"], agents)

    def test_hook_files_point_to_existing_scripts(self):
        for path in sorted((ROOT / ".github" / "hooks").glob("*.json")):
            with self.subTest(hook=path.name):
                config = json.loads(path.read_text(encoding="utf-8"))
                for entries in config["hooks"].values():
                    for entry in entries:
                        for key in ("command", "windows", "linux", "osx"):
                            for script in re.findall(r"[\w./\\-]+\.py", entry.get(key, "")):
                                self.assertTrue((ROOT / script.replace("\\", "/")).is_file(), script)


class DocumentTests(unittest.TestCase):
    def test_relative_links_resolve(self):
        for path in workbench_files({".md"}):
            text = re.sub(r"(?ms)^[ \t]*(`{3,}).*?^[ \t]*\1\s*$", "", path.read_text(encoding="utf-8"))
            for target in re.findall(r"\]\(([^)\s]+)\)", text):
                if re.match(r"^(https?:|mailto:|#)", target):
                    continue
                with self.subTest(file=path.relative_to(ROOT).as_posix(), link=target):
                    self.assertTrue((path.parent / target.split("#", 1)[0]).exists())

    def test_no_secrets_in_workbench_files(self):
        for path in workbench_files(TEXT_SUFFIXES):
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in SECRET_PATTERNS:
                with self.subTest(file=path.relative_to(ROOT).as_posix(), pattern=pattern):
                    self.assertIsNone(re.search(pattern, text))

    def test_private_folders_are_ignored_by_git(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for entry in (".env", "data/", "working/", "sources/", "vendor/", ".agents/"):
            self.assertIn(entry, ignored)


class AddonConfigTests(unittest.TestCase):
    def test_addons_are_pinned_licensed_described_and_safe(self):
        from agent_workbench.services import addons

        configured = addons.load_addons(ROOT)
        instructions = INSTRUCTIONS.read_text(encoding="utf-8")
        own_skills = {folder.name for folder in skill_folders()}
        self.assertTrue(configured)
        for name, addon in configured.items():
            with self.subTest(addon=name):
                self.assertTrue(addon["url"].startswith("https://"))
                self.assertTrue(addon.get("purpose"))
                self.assertIn(name, instructions)
                self.assertFalse(set(addon.get("skills", [])) & (CONFLICTING_ADDON_SKILLS | own_skills))


if __name__ == "__main__":
    unittest.main()
