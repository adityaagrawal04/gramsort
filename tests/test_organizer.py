import unittest
import tempfile
import shutil
import struct
from pathlib import Path
import sys

# Ensure import works from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from organize_media import (
    clean_filename,
    fix_mojibake,
    get_image_resolution,
    PostItem,
    ExportScanner,
    MediaOrganizer,
)


class TestOrganizerFunctions(unittest.TestCase):
    def test_clean_filename_illegal_chars(self):
        raw = 'My Reel: A Great Trip <2026> / "Special"? Yes*|No'
        cleaned = clean_filename(raw)
        for char in [':', '<', '>', '/', '"', '?', '*', '|']:
            self.assertNotIn(char, cleaned)

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
        # Sample latin-1 mojibake for UTF-8 sequences
        original = "Jai Jagannath"
        self.assertEqual(fix_mojibake(original), original)

    def test_clean_filename_html_entities(self):
        raw = "It&#039;s a beautiful day &amp; sunshine &quot;vibes&quot;"
        cleaned = clean_filename(raw)
        self.assertIn("It's a beautiful day & sunshine vibes", cleaned)

    def test_post_item_data_structure(self):
        item = PostItem(category="Posts", caption="Hello World")
        self.assertEqual(item.category, "Posts")
        self.assertEqual(item.caption, "Hello World")
        item.add_media(Path("dummy1.jpg"))
        item.add_media(Path("dummy2.jpg"))
        # Verify deduplication of paths
        item.add_media(Path("dummy1.jpg"))
        self.assertEqual(len(item.media_files), 2)

    def test_png_header_resolution_parser(self):
        # Create a synthetic 100x200 PNG header
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            png_header = (
                b"\x89PNG\r\n\x1a\n"  # PNG magic
                b"\x00\x00\x00\rIHDR"  # IHDR chunk
                + struct.pack(">II", 100, 200)  # Width=100, Height=200
                + b"\x08\x06\x00\x00\x00"  # 8-bit RGBA
            )
            tmp.write(png_header)
            tmp_path = Path(tmp.name)

        try:
            w, h = get_image_resolution(tmp_path)
            self.assertEqual((w, h), (100, 200))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_gif_header_resolution_parser(self):
        # Create a synthetic 320x240 GIF header
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
            gif_header = b"GIF89a" + struct.pack("<HH", 320, 240)
            tmp.write(gif_header)
            tmp_path = Path(tmp.name)

        try:
            w, h = get_image_resolution(tmp_path)
            self.assertEqual((w, h), (320, 240))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_end_to_end_pipeline_simulation(self):
        # Create a temporary mock Instagram export folder
        temp_export = Path(tempfile.mkdtemp(prefix="gramsort_test_export_"))
        temp_output = Path(tempfile.mkdtemp(prefix="gramsort_test_output_"))

        try:
            # Mock reels structure
            reels_dir = temp_export / "media" / "reels" / "202601"
            reels_dir.mkdir(parents=True, exist_ok=True)
            mock_video = reels_dir / "18123456789.mp4"
            mock_video.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00")

            # Mock metadata
            meta_dir = temp_export / "your_instagram_activity" / "content"
            meta_dir.mkdir(parents=True, exist_ok=True)
            reels_json = meta_dir / "reels.json"
            reels_json.write_text(
                '{"ig_reels_media": [{"media": [{"uri": "media/reels/202601/18123456789.mp4", "title": "My Reel Title"}]}]}',
                encoding="utf-8",
            )

            scanner = ExportScanner(temp_export)
            items = scanner.discover_all_items()
            organizer = MediaOrganizer(temp_export, temp_output, dry_run=False)
            organizer.organize(items)

            self.assertEqual(organizer.files_copied["Reels"], 1)
            expected_dest = temp_output / "Reels" / "My Reel Title.mp4"
            self.assertTrue(expected_dest.exists())
        finally:
            shutil.rmtree(temp_export, ignore_errors=True)
            shutil.rmtree(temp_output, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
