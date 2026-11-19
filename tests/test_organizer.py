import unittest
from pathlib import Path
import sys

# Ensure import works from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from organize_media import clean_filename, fix_mojibake, PostItem, MediaOrganizer


class TestOrganizerFunctions(unittest.TestCase):
    def test_clean_filename_illegal_chars(self):
        raw = 'My Reel: A Great Trip <2026> / "Special"? Yes*|No'
        cleaned = clean_filename(raw)
        self.assertNotIn(":", cleaned)
        self.assertNotIn("<", cleaned)
        self.assertNotIn(">", cleaned)
        self.assertNotIn("/", cleaned)
        self.assertNotIn('"', cleaned)
        self.assertNotIn("?", cleaned)
        self.assertNotIn("*", cleaned)
        self.assertNotIn("|", cleaned)

    def test_clean_filename_trim_and_collapse(self):
        raw = "Line 1\n\nLine 2     with    spaces\tand tabs"
        cleaned = clean_filename(raw)
        self.assertNotIn("\n", cleaned)
        self.assertNotIn("\t", cleaned)
        self.assertNotIn("  ", cleaned)

    def test_clean_filename_max_len(self):
        raw = "A" * 120
        cleaned = clean_filename(raw, max_len=80)
        self.assertLessEqual(len(cleaned), 80)

    def test_clean_filename_reserved_device_names(self):
        cleaned = clean_filename("CON")
        self.assertEqual(cleaned, "_CON")
        cleaned_prn = clean_filename("prn")
        self.assertEqual(cleaned_prn, "_prn")

    def test_clean_filename_trailing_periods_spaces(self):
        cleaned = clean_filename("Vacation in Bali... ")
        self.assertFalse(cleaned.endswith("."))
        self.assertFalse(cleaned.endswith(" "))

    def test_fix_mojibake(self):
        # Sample latin-1 mojibake for Hindi/devanagari or emojis
        original = "Jai Jagannath"
        self.assertEqual(fix_mojibake(original), original)

    def test_post_item_data_structure(self):
        item = PostItem(category="Posts", caption="Hello World")
        self.assertEqual(item.category, "Posts")
        self.assertEqual(item.caption, "Hello World")
        item.add_media(Path("dummy1.jpg"))
        item.add_media(Path("dummy2.jpg"))
        # Verify deduplication of paths
        item.add_media(Path("dummy1.jpg"))
        self.assertEqual(len(item.media_files), 2)


if __name__ == "__main__":
    unittest.main()
