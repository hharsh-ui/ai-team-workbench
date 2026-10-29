import os
import unittest
from unittest import mock

from support import temporary_root

from agent_workbench.services import lessons, session, session_log


class SessionLogTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_root(self)

    def test_newest_first(self):
        session_log.add_entry("Older", ["one"], "2026-01-01", root=self.root)
        session_log.add_entry("Newer", ["two", "three"], "2026-01-02", root=self.root)
        entries = session_log.recent_entries(5, self.root)
        self.assertEqual([entry["title"] for entry in entries], ["Newer", "Older"])
        self.assertIn("- three", entries[0]["text"])
        self.assertTrue(session_log.log_path(self.root).read_text(encoding="utf-8").startswith("# Session Log\n\n## [2026-01-02]"))

    def test_requires_points(self):
        with self.assertRaises(ValueError):
            session_log.add_entry("Empty", [" "], root=self.root)


class LessonTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_root(self)

    def test_add_and_search(self):
        lessons.add_lesson("Port in use", "FIXED", "Server fails to start", "Old process", "Stop it", date="2026-01-01", root=self.root)
        lessons.add_lesson("Quote rule", "rule", "Broken command", rule="Use single quotes", date="2026-01-02", root=self.root)
        text = lessons.ledger_path(self.root).read_text(encoding="utf-8")
        self.assertLess(text.index("Quote rule"), text.index("Port in use"))
        self.assertLess(text.index("---"), text.index("Quote rule"))
        found = lessons.search_lessons("server START", self.root)
        self.assertEqual([entry["title"] for entry in found], ["Port in use"])
        self.assertEqual(found[0]["status"], "FIXED")
        self.assertEqual(lessons.count_lessons(self.root), 2)

    def test_search_ranks_best_match_first(self):
        lessons.add_lesson("Port in use", "FIXED", "Server fails to start", "Old process", "Stop it", date="2026-01-01", root=self.root)
        lessons.add_lesson("Quote rule", "RULE", "Broken command", rule="Use single quotes", date="2026-01-02", root=self.root)
        lessons.add_lesson("Server quote escaping", "RULE", "Server command broke", rule="Quote paths", date="2026-01-03", root=self.root)
        found = lessons.search_lessons("how to quote the server", self.root)
        self.assertEqual([entry["title"] for entry in found], ["Server quote escaping", "Quote rule", "Port in use"])
        self.assertGreater(found[0]["score"], found[1]["score"])
        self.assertGreater(found[1]["score"], found[2]["score"])
        self.assertEqual(found[0]["matched"], ["quote", "server"])
        self.assertEqual(lessons.search_lessons("broke start", self.root)[0]["title"], "Port in use")
        self.assertEqual(lessons.search_lessons("art", self.root), [])
        self.assertEqual([entry["title"] for entry in lessons.search_lessons("", self.root, limit=2)],
                         ["Server quote escaping", "Quote rule"])

    def test_rejects_unknown_status(self):
        with self.assertRaises(ValueError):
            lessons.add_lesson("X", "MAYBE", "Y", root=self.root)


class SessionStartTests(unittest.TestCase):
    def test_first_name_handles_both_name_orders(self):
        self.assertEqual(session.first_name("Jane Doe"), "Jane")
        self.assertEqual(session.first_name("Doe, Jane"), "Jane")
        self.assertEqual(session.first_name("  "), "")

    def test_name_from_env_file_and_open_areas(self):
        root = temporary_root(self)
        (root / ".env").write_text("USER_FIRST_NAME=Sam\n", encoding="utf-8")
        environment = {key: value for key, value in os.environ.items() if key != "USER_FIRST_NAME"}
        with mock.patch.dict(os.environ, environment, clear=True):
            result = session.session_start(root=root)
        self.assertEqual(result["user_first_name"], "Sam")
        self.assertEqual(result["open_work_areas"], [])
        self.assertEqual(result["recent_sessions"], [])


if __name__ == "__main__":
    unittest.main()
