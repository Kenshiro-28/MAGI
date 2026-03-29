"""
test_codex_operations.py — Comprehensive integration test suite for codex_operations.py

Each test uses an isolated temporary codex.json; the real file is never touched.
Run with: python test_codex_operations.py
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

# Module under test
import codex_operations as _codex_module


class CodexTestBase(unittest.TestCase):
    """Base class: sets up a fresh temp codex file for every test."""

    @classmethod
    def setUpClass(cls):
        """Load the model once for all tests (avoids repeated downloads)."""
        _codex_module._get_model()

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w", encoding="utf-8"
        )
        self.temp_file.write("[]")
        self.temp_file.close()
        self.original_codex_file = _codex_module.CODEX_FILE
        _codex_module.CODEX_FILE = self.temp_file.name

    def tearDown(self):
        _codex_module.CODEX_FILE = self.original_codex_file

        try:
            os.unlink(self.temp_file.name)
        except FileNotFoundError:
            pass

        # Remove any quarantine backups left behind
        dir_name = os.path.dirname(self.temp_file.name)
        base_name = os.path.basename(self.temp_file.name)
        backup_pattern = f"{base_name}.corrupt_"
        for f in os.listdir(dir_name):
            if f.startswith(backup_pattern):
                try:
                    os.unlink(os.path.join(dir_name, f))
                except OSError:
                    pass

    # Convenience wrappers
    def write(self, title, content, tags="test"):
        return _codex_module.write_codex(title, content, tags)

    def read(self, query):
        return _codex_module.read_codex(query)

    def delete(self, title):
        return _codex_module.delete_codex(title)

    def raw_entries(self) -> list:
        """Read raw JSON from the temp file."""
        with open(_codex_module.CODEX_FILE, encoding="utf-8") as f:
            return json.load(f)


# -----------------------------------------------------------------------------
class TestWrite(CodexTestBase):

    def test_new_entry_saved(self):
        result = self.write("Python quicksort",
                            "def qs(a): return a if len(a)<=1 else qs([x for x in a[1:] if x<=a[0]])+[a[0]]+qs([x for x in a[1:] if x>a[0]])",
                            "python,algorithm")
        self.assertIn("Entry saved", result)
        self.assertIn("Python quicksort", result)

    def test_new_entry_persisted_to_disk(self):
        self.write("Disk persistence test", "content here", "test")
        raw = self.raw_entries()
        self.assertEqual(len(raw), 1)
        self.assertEqual(raw[0]["title"], "Disk persistence test")

    def test_new_entry_has_required_fields(self):
        self.write("Field check", "some content", "meta")
        entry = self.raw_entries()[0]
        required = {"title", "content", "tags", "created", "updated", "hash", "embedding"}
        self.assertTrue(required.issubset(entry.keys()))

    def test_tags_normalized_to_lowercase(self):
        self.write("Tag case test", "content", "Python, API, REST")
        entry = self.raw_entries()[0]
        self.assertEqual(entry["tags"], ["api", "python", "rest"])

    def test_tags_strips_whitespace(self):
        self.write("Tag whitespace", "content", "  a  ,  b  ,  c  ")
        self.assertEqual(self.raw_entries()[0]["tags"], ["a", "b", "c"])

    def test_content_too_long_rejected(self):
        long_content = "x" * (_codex_module._MAX_ENTRY_CHARS + 1)
        result = self.write("Overflow test", long_content, "test")
        self.assertIn("too long", result)
        self.assertEqual(len(self.raw_entries()), 0)

    def test_content_exactly_at_limit_accepted(self):
        content = "x" * _codex_module._MAX_ENTRY_CHARS
        result = self.write("At limit", content, "test")
        self.assertIn("Entry saved", result)

    def test_title_too_long_rejected(self):
        long_title = "x" * (_codex_module._MAX_TITLE_CHARS + 1)
        result = self.write(long_title, "content", "test")
        self.assertIn("too long", result)
        self.assertEqual(len(self.raw_entries()), 0)

    def test_verbatim_duplicate_blocked_by_hash(self):
        """Hash match fires before title check — same content, different title is blocked."""
        content = "identical content string"
        self.write("Original", content, "test")
        result = self.write("Copy (different title)", content, "test")
        self.assertIn("Identical content", result)
        self.assertIn("Skipped", result)
        self.assertEqual(len(self.raw_entries()), 1)

    def test_verbatim_duplicate_same_title_blocked_by_hash(self):
        """Hash match fires before title match — same title and content is blocked at hash check."""
        content = "same content"
        self.write("Title", content, "test")
        result = self.write("Title", content, "test")
        self.assertIn("Identical content", result)
        self.assertEqual(len(self.raw_entries()), 1)

    def test_title_match_updates_in_place(self):
        self.write("Update me", "version 1", "test")
        result = self.write("Update me", "version 2", "test,v2")
        self.assertIn("updated", result.lower())
        raw = self.raw_entries()
        self.assertEqual(len(raw), 1)
        self.assertEqual(raw[0]["content"], "version 2")
        self.assertEqual(raw[0]["tags"], ["test", "v2"])

    def test_title_match_case_insensitive(self):
        self.write("Case Title", "v1", "test")
        self.write("case title", "v2", "test")
        self.assertEqual(len(self.raw_entries()), 1)
        self.assertEqual(self.raw_entries()[0]["content"], "v2")

    def test_two_distinct_entries_both_saved(self):
        self.write("Alpha entry", "cooking recipes and meal preparation", "food")
        self.write("Beta entry", "spacecraft orbital mechanics and propulsion", "space")
        self.assertEqual(len(self.raw_entries()), 2)

    def test_semantic_duplicate_blocked(self):
        """Force a high cosine similarity to trigger duplicate warning."""
        self.write("Original entry", "some content about Python web scraping")
        with patch("codex_operations._cosine", return_value=0.95):
            result = self.write("Near duplicate", "similar content about Python web scraping")
        self.assertIn("Likely duplicate detected", result)
        self.assertEqual(len(self.raw_entries()), 1)

    def test_semantic_similar_note_shown(self):
        """Similarity above _SIMILAR_THRESHOLD but below _DUPLICATE_THRESHOLD adds a note."""
        self.write("Original entry", "some content about Python web scraping")
        with patch("codex_operations._cosine", return_value=0.80):
            result = self.write("Related entry", "different content about Python scraping tools")
        self.assertIn("semantically related", result)
        self.assertEqual(len(self.raw_entries()), 2)


# -----------------------------------------------------------------------------
class TestRead(CodexTestBase):

    def setUp(self):
        super().setUp()
        self.write("Python requests tutorial",
                   "Use requests.get(url) to fetch HTTP data. Handle errors with response.raise_for_status().",
                   "python,http,requests")
        self.write("Solana RPC calls",
                   "Use solana.rpc.api.Client to query on-chain data. getAccountInfo returns base64-encoded account data.",
                   "solana,blockchain,rpc")
        self.write("MAGI agent prompt design",
                   "Captain issues missions. Soldier executes. Use binary YES/NO evaluation to gate task completion.",
                   "magi,prompt,agent")

    def test_empty_codex_message(self):
        with open(_codex_module.CODEX_FILE, "w") as f:
            json.dump([], f)
        result = self.read("anything")
        self.assertEqual(result, _codex_module.CODEX_NO_RESULT)

    def test_read_list_all_entries(self):
        result = self.read(_codex_module.CODEX_LIST_ALL)
        self.assertIn("3 entries stored", result)
        self.assertIn("Python requests tutorial", result)
        self.assertIn("Solana RPC calls", result)
        self.assertIn("MAGI agent prompt design", result)

    def test_read_no_query_does_not_return_content_body(self):
        result = self.read(_codex_module.CODEX_LIST_ALL)
        self.assertNotIn("requests.get(url)", result)

    def test_semantic_query_returns_relevant_entry(self):
        result = self.read("HTTP fetch with Python")
        self.assertIn("Python requests tutorial", result)

    def test_semantic_query_top_result_is_most_relevant(self):
        result = self.read("HTTP fetch with Python")
        lines = result.split("\n")
        first_entry_line = next((line for line in lines if "---" in line), "")
        self.assertIn("Python requests tutorial", first_entry_line)

    def test_unrelated_query_returns_no_results(self):
        result = self.read("medieval castle architecture history")
        self.assertEqual(result, _codex_module.CODEX_NO_RESULT)

    def test_relevance_scores_shown(self):
        result = self.read("Solana blockchain")
        self.assertIn("relevance:", result)

    def test_max_results_respected(self):
        for i in range(6):
            self.write(f"Extra entry {i}",
                       f"Python data processing pipeline step {i} using pandas and numpy",
                       f"python,data,etl,step{i}")
        result = self.read("Python data ETL pipeline")
        count = result.count("relevance:")
        self.assertLessEqual(count, _codex_module._MAX_READ_RESULTS)


# -----------------------------------------------------------------------------
class TestDelete(CodexTestBase):

    def setUp(self):
        super().setUp()
        self.write("Keep this", "important knowledge", "keep")
        self.write("Delete this", "temporary stuff", "temp")

    def test_delete_removes_entry(self):
        result = self.delete("Delete this")
        self.assertIn("deleted", result.lower())
        titles = [e["title"] for e in self.raw_entries()]
        self.assertNotIn("Delete this", titles)

    def test_delete_preserves_other_entries(self):
        self.delete("Delete this")
        titles = [e["title"] for e in self.raw_entries()]
        self.assertIn("Keep this", titles)

    def test_delete_case_insensitive(self):
        result = self.delete("DELETE THIS")
        self.assertIn("deleted", result.lower())
        self.assertEqual(len(self.raw_entries()), 1)

    def test_delete_nonexistent_returns_error(self):
        result = self.delete("Ghost entry")
        self.assertIn("No entry found", result)

    def test_delete_nonexistent_suggests_alternatives(self):
        result = self.delete("Delet this")  # typo
        self.assertIn("Did you mean", result)

    def test_delete_empty_codex(self):
        with open(_codex_module.CODEX_FILE, "w") as f:
            json.dump([], f)
        result = self.delete("Anything")
        self.assertIn("No entry found", result)

    def test_delete_then_rewrite(self):
        """After deleting, the same title can be written again as a new entry."""
        self.delete("Delete this")
        result = self.write("Delete this", "brand new content", "new")
        self.assertIn("Entry saved", result)
        self.assertEqual(len(self.raw_entries()), 2)


# -----------------------------------------------------------------------------
class TestEdgeCases(CodexTestBase):

    def test_empty_tags_string(self):
        result = self.write("No tags entry", "content without tags", "")
        self.assertIn("Entry saved", result)
        self.assertEqual(self.raw_entries()[0]["tags"], [])

    def test_unicode_content(self):
        result = self.write("Unicode test", "綾波レイ — Ayanami Rei — 零 — テスト", "unicode,japanese")
        self.assertIn("Entry saved", result)
        self.assertEqual(self.raw_entries()[0]["content"], "綾波レイ — Ayanami Rei — 零 — テスト")

    def test_unicode_title(self):
        result = self.write("MAGI システム", "Multi-agent system inspired by NGE", "magi,nge")
        self.assertIn("Entry saved", result)

    def test_corrupted_json_handled_gracefully(self):
        with open(_codex_module.CODEX_FILE, "w") as f:
            f.write("{ this is not valid json }")
        result = self.read("anything")
        self.assertEqual(result, _codex_module.CODEX_NO_RESULT)

    def test_quarantine_backup_created_on_corruption(self):
        corrupt_content = "garbage"
        with open(_codex_module.CODEX_FILE, "w") as f:
            f.write(corrupt_content)

        self.read("anything")

        dir_name = os.path.dirname(_codex_module.CODEX_FILE)
        base_name = os.path.basename(_codex_module.CODEX_FILE)
        backup_pattern = f"{base_name}.corrupt_"
        backups = [f for f in os.listdir(dir_name) if f.startswith(backup_pattern)]
        self.assertGreater(len(backups), 0, "No quarantine backup created")

    def test_write_after_corrupt_json_recovers(self):
        with open(_codex_module.CODEX_FILE, "w") as f:
            f.write("CORRUPTED")
        result = self.write("Recovery test", "saved after corruption", "test")
        self.assertIn("Entry saved", result)
        self.assertEqual(len(self.raw_entries()), 1)

    def test_embedding_backfill_for_legacy_entries(self):
        """Entries without embeddings (hand-edited JSON) get embeddings on next access."""
        legacy = [{
            "title": "Legacy entry",
            "content": "Old content without embedding",
            "tags": ["legacy"],
            "created": "2024-01-01 00:00",
            "updated": "2024-01-01 00:00",
            "hash": "abc123"
        }]
        with open(_codex_module.CODEX_FILE, "w") as f:
            json.dump(legacy, f)

        self.read("legacy old content")
        raw = self.raw_entries()
        self.assertIn("embedding", raw[0])
        self.assertEqual(len(raw[0]["embedding"]), 1024)

    def test_embedding_dimension(self):
        """Newly created entries have the expected vector length."""
        self.write("Dim check", "some code")
        emb = self.raw_entries()[0]["embedding"]
        self.assertEqual(len(emb), 1024)

    def test_long_content_embedding_dimension(self):
        """Chunked-averaged embeddings have the same dimension as single-chunk embeddings."""
        content = "def foo(): pass\n" * 2100  # ~33600 chars, exceeds _CHUNK_SIZE=32000
        self.write("Chunked embed dim", content[:_codex_module._MAX_ENTRY_CHARS], "python")
        emb = self.raw_entries()[0]["embedding"]
        self.assertEqual(len(emb), 1024)

    def test_write_returns_string(self):
        self.assertIsInstance(self.write("Type check", "content", "test"), str)

    def test_read_returns_string(self):
        self.write("Type check", "content", "test")
        self.assertIsInstance(self.read("content"), str)

    def test_delete_returns_string(self):
        self.write("Type check", "content", "test")
        self.assertIsInstance(self.delete("Type check"), str)

    def test_invalid_entry_in_codex_skipped_gracefully(self):
        """A malformed entry in the JSON does not crash read or write."""
        malformed = [
            {"title": "Valid entry", "content": "good content", "tags": ["ok"],
             "created": "2024-01-01 00:00", "updated": "2024-01-01 00:00",
             "hash": "aabbccdd", "embedding": [0.1] * 1024},
            {"broken": True}  # missing required fields
        ]
        with open(_codex_module.CODEX_FILE, "w") as f:
            json.dump(malformed, f)

        # Use CODEX_LIST_ALL to trigger index listing
        # on the synthetic embedding — this directly verifies the valid entry is accessible
        result = self.read(_codex_module.CODEX_LIST_ALL)
        self.assertIn("Valid entry", result)

        result = self.write("New entry", "new content after malformed", "test")
        self.assertIn("Entry saved", result)


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Codex Test Suite")
    print("Model will load once at the start (if not already cached)...")
    print("=" * 60)
    unittest.main(verbosity=2)
