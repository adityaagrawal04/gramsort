#!/usr/bin/env python3
"""
Instagram Media Organizer
A command-line tool to organize Instagram export archives into Reels, Posts, and Stories
with Windows-safe renaming and quality-based deduplication.
"""

import os
import sys
import re
import json
import html
import shutil
import struct
import hashlib
import logging
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("MediaOrganizer")

MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".m4v", ".heic"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt"}

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def fix_mojibake(text: str) -> str:
    """Repair common Latin-1 decoded UTF-8 sequences."""
    if not text:
        return ""
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def clean_filename(text: Optional[str], max_len: int = 80) -> str:
    """Sanitize strings for Windows file and folder names."""
    if not text:
        return ""

    cleaned = html.unescape(text)
    cleaned = fix_mojibake(cleaned)
    cleaned = re.sub(r'[\\/:*?"<>|]', ' ', cleaned)
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if not cleaned:
        return ""

    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].strip()

    cleaned = cleaned.rstrip('. ')
    base_check = cleaned.split('.')[0].upper()
    if base_check in WINDOWS_RESERVED_NAMES:
        cleaned = f"_{cleaned}"

    return cleaned


def win_path(p: Path) -> Path:
    """Safely handle extended-length Windows paths."""
    try:
        s = str(p.resolve())
        if sys.platform == "win32" and not s.startswith("\\\\?\\") and len(s) >= 240:
            return Path("\\\\?\\" + s)
    except Exception:
        pass
    return p


def get_mp4_resolution(file_path: Path) -> Tuple[int, int]:
    """Pure-Python ISO BMFF header parser for video width and height."""
    try:
        with open(file_path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(0)

            def read_boxes(offset: int, end: int):
                boxes = []
                f.seek(offset)
                while f.tell() < end:
                    pos = f.tell()
                    header = f.read(8)
                    if len(header) < 8:
                        break
                    size, btype = struct.unpack(">I4s", header)
                    btype = btype.decode("latin1", errors="ignore")
                    if size == 1:
                        size_header = f.read(8)
                        if len(size_header) < 8:
                            break
                        size = struct.unpack(">Q", size_header)[0]
                        data_start = pos + 16
                    elif size == 0:
                        size = end - pos
                        data_start = pos + 8
                    else:
                        data_start = pos + 8
                    if size < 8:
                        break
                    boxes.append((btype, pos, data_start, pos + size))
                    f.seek(pos + size)
                return boxes

            root_boxes = read_boxes(0, file_size)
            moov = next((b for b in root_boxes if b[0] == "moov"), None)
            if not moov:
                return (0, 0)

            moov_boxes = read_boxes(moov[2], moov[3])
            traks = [b for b in moov_boxes if b[0] == "trak"]

            best_res = (0, 0)
            for trak in traks:
                trak_boxes = read_boxes(trak[2], trak[3])
                tkhd = next((b for b in trak_boxes if b[0] == "tkhd"), None)
                if tkhd:
                    f.seek(tkhd[2])
                    version = struct.unpack(">B", f.read(1))[0]
                    offset_wh = 84 if version == 1 else 76
                    f.seek(tkhd[2] + offset_wh)
                    wh_data = f.read(8)
                    if len(wh_data) == 8:
                        w_fixed, h_fixed = struct.unpack(">II", wh_data)
                        w = w_fixed >> 16
                        h = h_fixed >> 16
                        if (w * h) > (best_res[0] * best_res[1]):
                            best_res = (w, h)
            return best_res
    except Exception:
        return (0, 0)


def get_image_resolution(file_path: Path) -> Tuple[int, int]:
    """Extract image resolution using Pillow when installed, or pure-Python headers."""
    try:
        from PIL import Image
        with Image.open(file_path) as im:
            return im.size
    except Exception:
        pass

    try:
        with open(file_path, "rb") as f:
            head = f.read(64)
            if head.startswith(b"\x89PNG\r\n\x1a\n"):
                return struct.unpack(">II", head[16:24])
            if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
                return struct.unpack("<HH", head[6:10])
            if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
                vp8 = head[12:16]
                if vp8 == b"VP8 ":
                    f.seek(26)
                    w, h = struct.unpack("<HH", f.read(4))
                    return (w & 0x3FFF, h & 0x3FFF)
                elif vp8 == b"VP8L":
                    f.seek(21)
                    b = f.read(4)
                    return (1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6)))
                elif vp8 == b"VP8X":
                    f.seek(24)
                    b = f.read(6)
                    return (1 + (b[0] | (b[1] << 8) | (b[2] << 16)), 1 + (b[3] | (b[4] << 8) | (b[5] << 16)))
            f.seek(0)
            if f.read(2) == b"\xff\xd8":
                while True:
                    marker_header = f.read(2)
                    if len(marker_header) < 2 or marker_header[0] != 0xFF:
                        break
                    marker = marker_header[1]
                    while marker == 0xFF:
                        m = f.read(1)
                        if not m:
                            break
                        marker = m[0]
                    if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                        length = struct.unpack(">H", f.read(2))[0]
                        sof = f.read(length - 2)
                        h, w = struct.unpack(">HH", sof[1:5])
                        return (w, h)
                    elif marker in (0xD8, 0xD9):
                        continue
                    elif marker == 0xDA:
                        break
                    else:
                        length = struct.unpack(">H", f.read(2))[0]
                        f.seek(length - 2, 1)
    except Exception:
        pass
    return (0, 0)


def get_media_resolution(file_path: Path) -> Tuple[int, int]:
    ext = file_path.suffix.lower()
    if ext in {".mp4", ".mov", ".m4v"}:
        return get_mp4_resolution(file_path)
    return get_image_resolution(file_path)


def get_file_quality(file_path: Path) -> Tuple[int, int]:
    w, h = get_media_resolution(file_path)
    size = file_path.stat().st_size if file_path.exists() else 0
    return (w * h, size)


def compute_file_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class PostItem:
    def __init__(self, category: str, caption: Optional[str] = None):
        self.category = category
        self.caption = caption
        self.media_files: List[Path] = []
        self.subtitle_files: List[Path] = []

    def add_media(self, path: Path):
        if path not in self.media_files:
            self.media_files.append(path)

    def add_subtitle(self, path: Path):
        if path not in self.subtitle_files:
            self.subtitle_files.append(path)


class ExportScanner:
    def __init__(self, export_dir: Path):
        self.export_dir = export_dir
        self.disk_files_by_name: Dict[str, Path] = {}
        self.all_disk_media: List[Path] = []
        self.all_subtitles: Dict[str, Path] = {}
        self.media_by_category: Dict[str, List[Path]] = defaultdict(list)

    def scan_disk(self):
        logger.info("Scanning directory: %s", self.export_dir)
        count = 0
        for root, _, files in os.walk(self.export_dir):
            root_path = Path(root)
            for fname in files:
                ext = Path(fname).suffix.lower()
                full_path = root_path / fname
                if ext in MEDIA_EXTENSIONS:
                    self.disk_files_by_name[fname] = full_path
                    self.all_disk_media.append(full_path)
                    count += 1
                    parts_lower = [p.lower() for p in full_path.parts]
                    if "reels" in parts_lower:
                        self.media_by_category["Reels"].append(full_path)
                    elif "posts" in parts_lower or "archived_posts" in parts_lower:
                        self.media_by_category["Posts"].append(full_path)
                    elif "stories" in parts_lower:
                        self.media_by_category["Stories"].append(full_path)
                elif ext in SUBTITLE_EXTENSIONS:
                    self.all_subtitles[Path(fname).stem] = full_path

        logger.info("Indexed %d media files on disk.", count)

    def resolve_media_path(self, raw_path_str: str) -> Optional[Path]:
        if not raw_path_str:
            return None
        fname = Path(raw_path_str).name
        if fname in self.disk_files_by_name:
            return self.disk_files_by_name[fname]
        candidate = self.export_dir / raw_path_str
        if candidate.is_file():
            return candidate
        return None

    def find_companion_subtitle(self, media_path: Path) -> Optional[Path]:
        stem = media_path.stem
        if stem in self.all_subtitles:
            return self.all_subtitles[stem]
        for sub_ext in SUBTITLE_EXTENSIONS:
            cand = media_path.with_suffix(sub_ext)
            if cand.is_file():
                return cand
        return None

    def parse_html_entries(self, html_path: Path, category: str) -> List[PostItem]:
        items: List[PostItem] = []
        try:
            with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return items

        boxes = content.split('class="pam _3-95 _2ph- _a6-g uiBoxWhite noborder">')[1:]
        for box in boxes:
            caption = None
            h2_match = re.search(r'<h2[^>]*>(.*?)</h2>', box, re.DOTALL)
            if h2_match:
                cand = h2_match.group(1).strip()
                if cand not in {"Media", "Hashtags", "Place", "Reels", "Posts", "Stories"}:
                    caption = cand

            if not caption:
                cap_div = re.search(r'</a><div>([^<]+)</div>', box)
                if cap_div:
                    caption = cap_div.group(1).strip()

            raw_srcs = re.findall(r'<(?:img|video)[^>]+src=["\']([^"\']+)["\']', box)
            unique_srcs = list(dict.fromkeys(raw_srcs))

            resolved_files: List[Path] = []
            for src in unique_srcs:
                resolved = self.resolve_media_path(src)
                if resolved and resolved not in resolved_files:
                    resolved_files.append(resolved)

            if resolved_files:
                post_item = PostItem(category=category, caption=caption)
                for rf in resolved_files:
                    post_item.add_media(rf)
                    sub = self.find_companion_subtitle(rf)
                    if sub:
                        post_item.add_subtitle(sub)
                items.append(post_item)
        return items

    def parse_json_entries(self, json_path: Path, category: str) -> List[PostItem]:
        items: List[PostItem] = []
        try:
            with open(json_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
        except Exception:
            return items

        raw_entries = []
        if isinstance(data, list):
            raw_entries = data
        elif isinstance(data, dict):
            for key in ["ig_reels_media", "ig_stories", "ig_posts", "reels", "posts", "stories", "media"]:
                if key in data and isinstance(data[key], list):
                    raw_entries = data[key]
                    break
            if not raw_entries:
                raw_entries = [data]

        for entry in raw_entries:
            if not isinstance(entry, dict):
                continue
            caption = entry.get("title") or entry.get("caption")
            media_entries = entry.get("media") or entry.get("media_list") or [entry]
            if not isinstance(media_entries, list):
                media_entries = [media_entries]

            resolved_files: List[Path] = []
            for m in media_entries:
                if not isinstance(m, dict):
                    continue
                if not caption:
                    caption = m.get("title") or m.get("caption")
                uri = m.get("uri") or m.get("media_url") or m.get("path")
                if uri:
                    resolved = self.resolve_media_path(uri)
                    if resolved and resolved not in resolved_files:
                        resolved_files.append(resolved)

            if resolved_files:
                post_item = PostItem(category=category, caption=caption)
                for rf in resolved_files:
                    post_item.add_media(rf)
                    sub = self.find_companion_subtitle(rf)
                    if sub:
                        post_item.add_subtitle(sub)
                items.append(post_item)
        return items

    def is_media_metadata_file(self, path: Path) -> Optional[str]:
        stem = path.stem.lower()
        parent = path.parent.name.lower()
        if parent not in {"media", "content"}:
            if not (stem in {"reels", "stories", "archived_posts"} or stem.startswith("posts")):
                return None

        ignore_terms = {
            "comment", "like", "reaction", "viewed", "setting", "history",
            "interaction", "keyword", "search", "message", "chat", "topic",
            "advertiser", "autofill", "device", "login", "password", "saved",
            "interest", "hide", "guide", "repost"
        }
        if any(t in stem for t in ignore_terms):
            return None

        if "reel" in stem:
            return "Reels"
        elif "post" in stem or "archived" in stem:
            return "Posts"
        elif "stor" in stem:
            return "Stories"
        return None

    def discover_all_items(self) -> List[PostItem]:
        all_items: List[PostItem] = []
        claimed_media: Set[Path] = set()

        json_files, html_files = [], []
        for root, _, files in os.walk(self.export_dir):
            for fname in files:
                fpath = Path(root) / fname
                ext = fpath.suffix.lower()
                if ext == ".json":
                    json_files.append(fpath)
                elif ext == ".html":
                    html_files.append(fpath)

        for jf in json_files:
            cat = self.is_media_metadata_file(jf)
            if cat:
                entries = self.parse_json_entries(jf, cat)
                for item in entries:
                    all_items.append(item)
                    claimed_media.update(item.media_files)

        html_files.sort(key=lambda p: 0 if "posts_1" in p.name.lower() else 1)
        for hf in html_files:
            cat = self.is_media_metadata_file(hf)
            if cat:
                entries = self.parse_html_entries(hf, cat)
                for item in entries:
                    new_media = [m for m in item.media_files if m not in claimed_media]
                    if new_media:
                        item.media_files = new_media
                        all_items.append(item)
                        claimed_media.update(new_media)

        for cat in ["Reels", "Posts", "Stories"]:
            for f in self.media_by_category[cat]:
                if f not in claimed_media:
                    item = PostItem(category=cat, caption=None)
                    item.add_media(f)
                    sub = self.find_companion_subtitle(f)
                    if sub:
                        item.add_subtitle(sub)
                    all_items.append(item)
                    claimed_media.add(f)

        return all_items


class MediaOrganizer:
    def __init__(self, export_dir: Path, output_dir: Path, dry_run: bool = False):
        self.export_dir = export_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.dry_run = dry_run

        self.files_copied: Dict[str, int] = {"Reels": 0, "Posts": 0, "Stories": 0}
        self.duplicates_resolved = 0
        self.items_without_caption = 0
        self.items_with_caption = 0

        self.dest_registry: Dict[Path, Tuple[Tuple[int, int], Path]] = {}
        self.seen_media_ids: Dict[str, Tuple[Path, Tuple[int, int], Path]] = {}
        self.file_size_cache: Dict[int, List[Tuple[Optional[str], Path, Path]]] = defaultdict(list)
        self.claimed_folders: Set[Path] = set()
        self.claimed_files: Set[Path] = set()

    def get_media_identifier(self, media_path: Path) -> str:
        stem = media_path.stem
        m = re.search(r'(\d{10,})', stem)
        return m.group(1) if m else stem

    def resolve_unique_folder(self, parent_dir: Path, base_name: str) -> Path:
        target = parent_dir / base_name
        counter = 1
        while target in self.claimed_folders or (not self.dry_run and target.exists()):
            target = parent_dir / f"{base_name}_{counter}"
            counter += 1
        self.claimed_folders.add(target)
        return target

    def resolve_unique_file(self, parent_dir: Path, base_name: str, ext: str) -> Path:
        target = parent_dir / f"{base_name}{ext}"
        counter = 1
        while target in self.claimed_files or (not self.dry_run and target.exists()):
            target = parent_dir / f"{base_name}_{counter}{ext}"
            counter += 1
        self.claimed_files.add(target)
        return target

    def transfer_file(self, src: Path, dst: Path, category: str):
        media_id = self.get_media_identifier(src)
        quality = get_file_quality(src)
        file_size = src.stat().st_size if src.exists() else 0

        if file_size in self.file_size_cache:
            content_hash = compute_file_hash(src)
            entries = self.file_size_cache[file_size]
            for idx, (existing_hash, existing_dst, existing_src) in enumerate(entries):
                if existing_hash is None:
                    existing_hash = compute_file_hash(existing_src)
                    entries[idx] = (existing_hash, existing_dst, existing_src)
                if content_hash == existing_hash:
                    self.duplicates_resolved += 1
                    existing_quality, _ = self.dest_registry.get(existing_dst, ((0, 0), Path("")))
                    if quality > existing_quality:
                        if not self.dry_run:
                            dst_safe = win_path(existing_dst)
                            src_safe = win_path(src)
                            dst_safe.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_safe, dst_safe)
                        self.dest_registry[existing_dst] = (quality, src)
                    return
            self.file_size_cache[file_size].append((content_hash, dst, src))
        else:
            self.file_size_cache[file_size].append((None, dst, src))

        if media_id in self.seen_media_ids:
            existing_dst, existing_quality, _ = self.seen_media_ids[media_id]
            self.duplicates_resolved += 1
            if quality > existing_quality:
                if not self.dry_run:
                    dst_safe = win_path(existing_dst)
                    src_safe = win_path(src)
                    dst_safe.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_safe, dst_safe)
                self.dest_registry[existing_dst] = (quality, src)
                self.seen_media_ids[media_id] = (existing_dst, quality, src)
            return

        if not self.dry_run:
            dst_safe = win_path(dst)
            src_safe = win_path(src)
            dst_safe.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_safe, dst_safe)

        self.dest_registry[dst] = (quality, src)
        self.seen_media_ids[media_id] = (dst, quality, src)
        self.claimed_files.add(dst)
        self.files_copied[category] += 1

    def copy_subtitle(self, sub_src: Path, media_dst: Path):
        sub_dst = media_dst.with_suffix(sub_src.suffix.lower())
        if not self.dry_run:
            sub_dst_safe = win_path(sub_dst)
            sub_src_safe = win_path(sub_src)
            sub_dst_safe.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sub_src_safe, sub_dst_safe)

    def organize(self, items: List[PostItem]):
        reels_dir = self.output_dir / "Reels"
        posts_dir = self.output_dir / "Posts"
        stories_dir = self.output_dir / "Stories"

        for item in items:
            has_caption = bool(item.caption and clean_filename(item.caption))
            if has_caption:
                self.items_with_caption += 1
                cleaned_name = clean_filename(item.caption, max_len=80)
            else:
                self.items_without_caption += 1
                cleaned_name = ""

            if item.category == "Reels":
                for media_file in item.media_files:
                    ext = media_file.suffix.lower()
                    dst = self.resolve_unique_file(reels_dir, cleaned_name or media_file.stem, ext)
                    self.transfer_file(media_file, dst, "Reels")
                    if item.subtitle_files:
                        self.copy_subtitle(item.subtitle_files[0], dst)

            elif item.category == "Posts":
                if len(item.media_files) > 1:
                    folder_name = cleaned_name or f"post_{item.media_files[0].stem}"
                    post_folder = self.resolve_unique_folder(posts_dir, folder_name)
                    for idx, media_file in enumerate(item.media_files, start=1):
                        ext = media_file.suffix.lower()
                        file_name = f"{cleaned_name}_{idx}{ext}" if cleaned_name else media_file.name
                        dst = post_folder / file_name
                        self.transfer_file(media_file, dst, "Posts")
                else:
                    media_file = item.media_files[0]
                    ext = media_file.suffix.lower()
                    dst = self.resolve_unique_file(posts_dir, cleaned_name or media_file.stem, ext)
                    self.transfer_file(media_file, dst, "Posts")

            elif item.category == "Stories":
                if len(item.media_files) > 1:
                    folder_name = cleaned_name or f"story_{item.media_files[0].stem}"
                    story_folder = self.resolve_unique_folder(stories_dir, folder_name)
                    for idx, media_file in enumerate(item.media_files, start=1):
                        ext = media_file.suffix.lower()
                        file_name = f"{cleaned_name}_{idx}{ext}" if cleaned_name else media_file.name
                        dst = story_folder / file_name
                        self.transfer_file(media_file, dst, "Stories")
                else:
                    media_file = item.media_files[0]
                    ext = media_file.suffix.lower()
                    dst = self.resolve_unique_file(stories_dir, cleaned_name or media_file.stem, ext)
                    self.transfer_file(media_file, dst, "Stories")

    def print_report(self):
        total_copied = sum(self.files_copied.values())
        sep = "=" * 70
        print(f"\n{sep}")
        print(" INSTAGRAM MEDIA ORGANIZATION REPORT ".center(70, "="))
        print(sep)
        print(f" Source Directory  : {self.export_dir}")
        print(f" Output Directory  : {self.output_dir}")
        print(f" Mode              : {'DRY RUN (Simulated)' if self.dry_run else 'EXECUTED (Files Copied)'}")
        print("-" * 70)
        print(f"  Folder 'Reels'   : {self.files_copied['Reels']:,} files")
        print(f"  Folder 'Posts'   : {self.files_copied['Posts']:,} files")
        print(f"  Folder 'Stories' : {self.files_copied['Stories']:,} files")
        print("-" * 70)
        print(f"  Total Files Organized        : {total_copied:,}")
        print(f"  Duplicates Resolved          : {self.duplicates_resolved:,}")
        print(f"  Items Matched to Caption     : {self.items_with_caption:,}")
        print(f"  Items Without Caption        : {self.items_without_caption:,}")
        print(f"{sep}\n")


def main():
    parser = argparse.ArgumentParser(description="Organize unzipped Instagram media export.")
    parser.add_argument("export_dir", help="Path to unzipped Instagram export folder")
    parser.add_argument("--output-dir", "-o", default=None, help="Target folder (default: Organized_Media beside export)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without copying files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debug logging")

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    export_path = Path(args.export_dir)
    if not export_path.exists():
        logger.error("Path does not exist: %s", export_path)
        sys.exit(1)

    output_path = Path(args.output_dir) if args.output_dir else export_path.parent / "Organized_Media"

    scanner = ExportScanner(export_path)
    scanner.scan_disk()
    items = scanner.discover_all_items()

    organizer = MediaOrganizer(export_path, output_path, args.dry_run)
    organizer.organize(items)
    organizer.print_report()


if __name__ == "__main__":
    main()
