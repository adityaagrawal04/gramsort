<div align="center">

# 📸 GramSort
### Intelligent Instagram Export Organizer & Resolution-Aware Deduplicator

[![CI](https://github.com/adityaagrawal04/gramsort/actions/workflows/ci.yml/badge.svg)](https://github.com/adityaagrawal04/gramsort/actions)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/adityaagrawal04/gramsort)
[![Dependencies](https://img.shields.io/badge/dependencies-Zero%20(Pure%20Standard%20Library)-brightgreen.svg)](https://github.com/adityaagrawal04/gramsort)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange.svg)](https://github.com/adityaagrawal04/gramsort/pulls)

*A zero-dependency, lightning-fast Python engine that organizes raw Instagram/Meta data exports into cleanly categorized, captioned, and deduplicated media libraries.*

[Key Features](#-key-features) • [Workflow](#-architecture--workflow) • [Before & After](#-before--after) • [How to Export Data](#-how-to-request-your-instagram-data) • [Quick Start](#-quick-start) • [CLI Reference](#-cli-reference) • [Engineering Deep-Dive](#-under-the-hood-engineering-highlights) • [Python API](#-python-api-integration) • [FAQ](#-frequently-asked-questions)

</div>

---

## 🧐 The Problem with Instagram Exports

When you download your archive from Instagram or the Meta Accounts Center, you receive gigabytes of unstructured, confusing data:

* **Cryptic Filenames:** Photos and videos are labeled with meaningless numeric IDs (e.g., `18139097890568540.mp4`, `17872717830626145.webp`).
* **Scattered & Split Archives:** Media files are buried across dozens of dated subdirectories (`202110/`, `202305/`) and split across multi-part zip archives (`part_1`, `part_2`, `part_3`).
* **Rampant Duplicate Bloat:** Stories, feed posts, archived memories, and cross-posts duplicate the same content at different compression levels.
* **Detached Captions & Subtitles:** Captions, dates, and `.srt` subtitle files are isolated in separate JSON or HTML metadata tables.

> **GramSort solves this in seconds.** It parses metadata, matches media to captions, groups multi-image carousels, pairs subtitle files, detects duplicates, compares resolution and file size, and copies the highest quality version into clean `Reels`, `Posts`, and `Stories` folders.

---

## 📁 Before & After

```text
BEFORE (Raw Instagram Export)                 AFTER GramSort
----------------------------------           -------------------------------------
📁 instagram-export/                         📁 Organized_Media/
├── 📁 part_1/                               ├── 📁 Reels/
│   ├── 📁 media/reels/202608/               │   ├── Never Travel with a train.mp4
│   │   ├── 18139097890568540.mp4            │   ├── Never Travel with a train.srt   <-- (Companion Subtitle)
│   │   └── 18139097890568540.srt            │   └── Bangkok Street Food Tour.mp4
│   └── 📁 your_instagram_activity/          ├── 📁 Posts/
│       └── reels.html                       │   ├── Golden Temple Amritsar.jpg
├── 📁 part_2/                               │   └── Thailand Vacation 2024/         <-- (Carousel Album)
│   └── 📁 media/posts/202310/               │       ├── Thailand Vacation 2024_1.webp
│       ├── 18012629246708407.jpg            │       ├── Thailand Vacation 2024_2.webp
│       └── 18264730594164112.jpg (duplicate)│       └── Thailand Vacation 2024_3.mp4
└── 📁 part_3/                               └── 📁 Stories/
    └── 📁 media/stories/202302/                 ├── Sunrise at Mount Batur.webp
        └── 18024061750469097.jpg                └── 18024061750469097.jpg           <-- (Fallback ID)
```

---

## 🔄 Architecture & Workflow

```mermaid
flowchart TD
    A["Raw Instagram Export Archive\n(Single or Multi-part Zip Folder)"] --> B["GramSort Discovery Engine"]
    B --> C1["Disk Media Indexer\n(.jpg, .webp, .mp4, .heic, .png)"]
    B --> C2["Metadata Engine\n(JSON & HTML Parser + Mojibake Fixer)"]
    C1 --> D["Media & Caption Associator"]
    C2 --> D
    D --> E["Quality Inspection Engine\n(Pure Python ISO-BMFF & Image Headers)"]
    E --> F{"Duplicate Evaluation\n(Media ID + Lazy SHA-256)"}
    F -- "Higher Quality Winner" --> G["Windows Path Hardener\n(Clean illegal chars, MAX_PATH, DOS names)"]
    F -- "Lower / Redundant Copy" --> H["Skip / Log Duplicate\n(Summary Report)"]
    G --> I["Destination Router"]
    I --> J["📁 Reels/ (Flat + Companion .srt)"]
    I --> K["📁 Posts/ (Singles & Carousel Subfolders)"]
    I --> L["📁 Stories/ (Singles & Slide Subfolders)"]
```

---

## ✨ Key Features

### 1. 📂 Three Dedicated Category Destinations
* **`Reels/`**: Flat folder containing every reel video. Companion subtitle files (`.srt`, `.vtt`) are identified and renamed to match the video.
* **`Posts/`**: Single posts are placed flat. Multi-photo and multi-video carousel posts are placed into dedicated subfolders named after the post caption.
* **`Stories/`**: Single-clip stories are placed flat; multi-item story sequences are grouped into dedicated subfolders.

### 2. ⚡ Zero-Dependency Video & Image Resolution Engine
* **No FFmpeg or external binaries required**: Features a built-in ISO Base Media File Format (ISO BMFF) binary parser written in pure Python that extracts MP4/MOV track header (`tkhd`) dimensions in milliseconds.
* **Header-based image dimension inspection**: Pure binary header decoding for JPEG (SOF0/SOF2 markers), PNG (IHDR), WEBP (VP8/VP8L/VP8X), and GIF. Pillow is supported if installed, but never required.

### 3. 🧠 Smart Two-Tier Quality Deduplication
* Eliminates identical media cross-posted across Stories, Feed, or Archives.
* Compares duplicates using:
  $$\text{Quality Score} = (\text{Total Pixels: } \text{width} \times \text{height}, \text{File Size in Bytes})$$
* **Lazy Hash Optimization**: SHA-256 checksums are computed only when two files share the exact same byte size, avoiding unnecessary disk reads on thousands of files.

### 4. 🔍 Dual-Format Metadata Compatibility
* Supports **both JSON** (`reels.json`, `posts_1.json`, `stories.json`) and **HTML** (`reels.html`, `posts_1.html`, `posts.html`, `stories.html`) export formats.
* Automatically repairs Meta's notorious **Latin-1 Mojibake bug** (e.g. `\u00c3\u00a9` $\rightarrow$ `é`, garbled emojis) and unescapes HTML entities (`&#039;` $\rightarrow$ `'`, `&amp;` $\rightarrow$ `&`).

### 5. 🪟 Windows Filesystem Resilience
* Strips illegal Windows characters (`\ / : * ? " < > |`) and control bytes.
* Protects against Windows reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).
* Truncates filenames cleanly to ~80 characters and strips trailing spaces/periods.
* Supports Windows extended-length paths (`\\?\` prefix) to prevent `MAX_PATH` (260 character) overflow errors.

### 6. 🔒 100% Non-Destructive Operation
* Never deletes, modifies, or moves files from your original export directory. All files are safely copied using `shutil.copy2` to preserve original modification timestamps and EXIF metadata.

---

## ⚡ Performance Comparison

| Feature | Manual Organization | Generic Shell / Batch Scripts | GramSort |
|---|:---:|:---:|:---:|
| **Processing Speed (7,000 files)** | Hours to Days | 2 to 5 minutes | **~10 seconds** |
| **External Dependencies** | N/A | FFmpeg, ExifTool, OpenCV | **Zero (Standard Library)** |
| **Resolution-Based Deduplication** | Eyeball / Guesswork | File size only | **Resolution + File Size** |
| **Carousel / Album Grouping** | Tedious manual sorting | Mixed into a single pile | **Automated Subfolders** |
| **Subtitle (.srt) Pairing** | Discarded or lost | Ignored | **Renamed & Preserved** |
| **Multi-Part Archive Support** | Manual unzipping & join | Fails on split paths | **Recursive Auto-Join** |
| **Windows Reserved Name Guard** | Crashes Explorer | Often unhandled | **Built-in Sanitization** |
| **Mojibake / Emoji Repair** | Garbled characters | Broken text | **Automatic UTF-8 Recovery** |

---

## 📥 How to Request Your Instagram Data

To export your raw Instagram media archive from Meta:

1. Open Instagram on your phone or browser $\rightarrow$ **Settings** $\rightarrow$ **Accounts Center**.
2. Select **Your information and permissions** $\rightarrow$ **Export your information**.
3. Choose your Instagram profile and click **Export all available information**.
4. Configure your export settings:
   * **Format**: Select either **JSON** or **HTML** *(GramSort seamlessly parses both)*.
   * **Media quality**: High.
   * **Date range**: All time.
5. Once Meta finishes generating your export, download the archive(s) and unzip them into a folder on your drive.

---

## 🚀 Quick Start

### Installation

No external dependencies are required. Clone the repository and run:

```bash
git clone https://github.com/adityaagrawal04/gramsort.git
cd gramsort
```

*(Optional)* Install Pillow if you want extended image codec support:
```bash
pip install -r requirements.txt
```

### Basic Usage

#### 1. Preview with Dry Run (Safe Simulation)
Simulate the run and inspect statistics without writing any files:
```bash
python organize_media.py "C:\path\to\instagram-export" --dry-run
```

#### 2. Run Organization
Organize media into a new `Organized_Media` folder placed right beside your export:
```bash
python organize_media.py "C:\path\to\instagram-export"
```

#### 3. Custom Output Directory
Specify an external drive or custom folder as the destination:
```bash
python organize_media.py "C:\path\to\instagram-export" --output-dir "D:\Backups\Organized_Media"
```

#### 4. Verbose Debug Logging
Enable detailed logging to inspect every parsed metadata file and matched path:
```bash
python organize_media.py "C:\path\to\instagram-export" -v
```

---

## 🛠️ CLI Reference

```text
usage: organize_media.py [-h] [--output-dir PATH] [--dry-run] [--verbose] export_dir

positional arguments:
  export_dir            Path to the unzipped Instagram export folder

options:
  -h, --help            Show this help message and exit
  --output-dir, -o PATH Target folder for organized media (default: Organized_Media beside export)
  --dry-run             Simulate execution and print report without writing files
  --verbose, -v         Enable detailed debug logging
```

---

## 🔬 Under the Hood: Engineering Highlights

### 1. Pure-Python ISO-BMFF Video Parser
Spawning external tools like `ffprobe` or `ffmpeg` for thousands of video files incurs massive process creation overhead. GramSort contains a lightweight, zero-dependency binary reader that directly navigates the ISO Base Media File Format:
1. Scans root-level atoms for the `moov` (movie) container box.
2. Locates all `trak` (track) child boxes.
3. Decodes the `tkhd` (track header) atom to extract the 16.16 fixed-point video width and height integers.
4. Returns the exact display resolution in under 1 millisecond per video.

### 2. Lazy Deduplication & Quality Metric
Instagram often exports identical photos cross-posted across your feed and stories. Simple filename hashing misses these duplicates because filenames are randomly generated. GramSort implements an optimal two-tier deduplicator:
* **Tier 1 (Media ID):** Extracts the underlying 10-19 digit Instagram media identifier from filenames (e.g. `18139097890568540`).
* **Tier 2 (Lazy SHA-256):** When media IDs differ but file sizes are identical, GramSort computes a chunked SHA-256 hash. Files with unique sizes skip hashing entirely, saving thousands of disk operations.
* **Winner Selection:** Conflicting items are scored by $(W \times H, \text{file size})$. The highest-resolution, largest file wins; the lower-resolution or recompressed version is discarded.

### 3. Automatic Mojibake & Emoji Recovery
Meta's export tools encode UTF-8 bytes into ISO-8859-1 (Latin-1) strings, producing mojibake in captions (e.g., `Ã©` instead of `é`, or broken emoji byte sequences). GramSort reverses this decoding artifact:
```python
def fix_mojibake(text: str) -> str:
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
```

---

## 🐍 Python API Integration

You can integrate GramSort directly into your own automation pipelines and scripts:

```python
from pathlib import Path
from organize_media import ExportScanner, MediaOrganizer

export_path = Path("C:/Downloads/instagram-export")
output_path = Path("D:/Organized_Media")

# 1. Discover all media and associated captions
scanner = ExportScanner(export_path)
items = scanner.discover_all_items()

# 2. Organize and deduplicate
organizer = MediaOrganizer(export_path, output_path, dry_run=False)
organizer.organize(items)

# 3. Print report
organizer.print_report()
```

---

## 📊 Sample Execution Report

```text
======================================================================
=========== INSTAGRAM & FACEBOOK MEDIA ORGANIZATION REPORT ===========
======================================================================
 Source Directory  : C:\Users\Lenovo\Downloads\instagram-export
 Output Directory  : C:\Users\Lenovo\Downloads\Organized_Media
 Mode              : EXECUTED (Files Copied)
----------------------------------------------------------------------
  Folder 'Reels'   : 119 files
  Folder 'Posts'   : 995 files
  Folder 'Stories' : 5,870 files
  -------------------------------------------------------------
  Total Files Organized        : 6,984
  Duplicates Resolved          : 75
  Items Matched to Caption     : 796
  Items Without Caption        : 5,673
======================================================================
 [SUCCESS] Media organization completed successfully!
======================================================================
```

---

## 🧪 Unit Tests

GramSort comes with a comprehensive standalone test suite verifying Windows path sanitization, mojibake decoding, binary header parsing, and pipeline simulation:

```bash
python -m unittest discover tests -v
```

---

## 💡 Frequently Asked Questions

<details>
<summary><b>Does GramSort modify or delete files in my original export?</b></summary>
<p>No. GramSort operates completely non-destructively. Files are read from the export and copied into the target directory using <code>shutil.copy2</code>, preserving original timestamps and file attributes.</p>
</details>

<details>
<summary><b>What if my Instagram export came in multiple ZIP parts?</b></summary>
<p>Instagram often splits large account downloads into multiple archives (e.g. part 1, part 2, part 3). If you unzip them into the same parent folder, GramSort recursively walks the entire tree and stitches them together seamlessly.</p>
</details>

<details>
<summary><b>Is my personal data sent anywhere?</b></summary>
<p>Never. GramSort runs 100% locally on your machine with zero network calls, zero telemetry, and zero third-party dependencies.</p>
</details>

<details>
<summary><b>Do I need ffmpeg installed to organize video reels?</b></summary>
<p>No. GramSort contains a custom, lightweight ISO BMFF binary parser that extracts video dimensions directly from MP4 and MOV headers without external binaries.</p>
</details>

<details>
<summary><b>What if two different posts have the same caption?</b></summary>
<p>GramSort detects filename collisions and appends an incremental numeric suffix (<code>_1</code>, <code>_2</code>) so no media is ever overwritten.</p>
</details>

<details>
<summary><b>What happens to posts or stories without captions?</b></summary>
<p>If an item has no caption or title in the metadata, GramSort cleanly retains its original export filename or ID.</p>
</details>

<details>
<summary><b>Does it work with Facebook data exports too?</b></summary>
<p>Yes. Meta uses the exact same HTML and JSON archive structure across both Facebook and Instagram data downloads.</p>
</details>

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/NewFeature`)
3. Commit your changes (`git commit -m 'Add NewFeature'`)
4. Push to the branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
