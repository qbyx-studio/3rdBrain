"""Focused regression tests for Telegram edit handling."""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


SOURCE_BOT = Path(__file__).resolve().parents[1] / "bot.py"


class BotEditTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        bot_path = root / "bot.py"
        shutil.copyfile(SOURCE_BOT, bot_path)
        (root / "config.json").write_text(
            json.dumps({"token": "test-token", "base_name": "MyBase"}),
            encoding="utf-8",
        )
        spec = importlib.util.spec_from_file_location("3rdbrain_inbox_bot_test", bot_path)
        self.bot = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.bot)
        self.bot.save(self.bot.INBOX, [])

    def tearDown(self):
        self.temp_dir.cleanup()

    def seed(self, item):
        self.bot.save(self.bot.INBOX, [item])

    def inbox(self):
        return self.bot.load(self.bot.INBOX, [])

    def test_pending_message_edit_replaces_text_and_trigger(self):
        self.bot.save(
            self.bot.INBOX,
            [
                {
                    "message_id": 10,
                    "chat_id": 20,
                    "date": 100,
                    "text": "old remark",
                    "processed": False,
                    "trigger": False,
                },
                {
                    "message_id": 10,
                    "chat_id": 21,
                    "date": 100,
                    "text": "other chat",
                    "processed": False,
                    "trigger": False,
                },
            ],
        )

        self.bot.apply_edit(20, 10, "Send this to MyBase", edit_date=110)

        item = self.inbox()[0]
        self.assertEqual(item["text"], "Send this to MyBase")
        self.assertEqual(item["edit_date"], 110)
        self.assertTrue(item["trigger"])
        self.assertFalse(item["processed"])
        self.assertEqual(len(self.inbox()), 2)
        self.assertEqual(self.inbox()[1]["text"], "other chat")

    def test_processed_message_edit_is_reopened(self):
        self.seed(
            {
                "message_id": 11,
                "chat_id": 20,
                "date": 100,
                "text": "old",
                "processed": True,
                "confirmed": True,
                "filed_as": "recipes/soup.md",
                "trigger": False,
            }
        )

        self.bot.apply_edit(20, 11, "new", edit_date=120)

        item = self.inbox()[0]
        self.assertEqual(item["previous_filed_as"], "recipes/soup.md")
        self.assertEqual(item["filed_as"], "")
        self.assertFalse(item["processed"])
        self.assertFalse(item["confirmed"])
        self.assertTrue(item["needs_review"])
        self.assertEqual(item["text"], "new")
        self.assertEqual(item["edit_date"], 120)

    def test_unseen_edit_is_captured(self):
        self.bot.apply_edit(20, 12, "missed original", edit_date=130, message_date=90)

        item = self.inbox()[0]
        self.assertEqual(item["captured_via"], "edit")
        self.assertEqual(item["date"], 90)
        self.assertEqual(item["edit_date"], 130)
        self.assertFalse(item["processed"])

    def test_duplicate_identical_edit_is_idempotent(self):
        self.bot.apply_edit(20, 13, "latest", edit_date=140, message_date=91)
        before = Path(self.bot.INBOX).read_bytes()

        changed = self.bot.apply_edit(20, 13, "latest", edit_date=140, message_date=91)

        self.assertFalse(changed)
        self.assertEqual(Path(self.bot.INBOX).read_bytes(), before)
        self.assertEqual(len(self.inbox()), 1)

    def test_edited_caption_is_used_as_message_text(self):
        text = self.bot.extract_message_text({"caption": "  revised caption  "})
        self.bot.apply_edit(20, 14, text, edit_date=150, message_date=92)

        self.assertEqual(self.inbox()[0]["text"], "revised caption")

    def test_newest_of_multiple_edits_wins(self):
        self.seed(
            {
                "message_id": 15,
                "chat_id": 20,
                "date": 100,
                "text": "original",
                "processed": False,
                "trigger": False,
            }
        )
        self.bot.apply_edit(20, 15, "first edit", edit_date=160)
        self.bot.apply_edit(20, 15, "latest edit", edit_date=170)
        self.bot.apply_edit(20, 15, "late stale delivery", edit_date=165)

        item = self.inbox()[0]
        self.assertEqual(item["text"], "latest edit")
        self.assertEqual(item["edit_date"], 170)
        self.assertEqual(self.bot.ALLOWED_UPDATES, ("message", "edited_message"))


if __name__ == "__main__":
    unittest.main()
