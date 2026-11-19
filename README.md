<div align="center">

# 📸 GramSort
### The Intelligent Instagram Data Export Organizer & Media Deduplicator

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/adityaagrawal04/gramsort)
[![Dependencies](https://img.shields.io/badge/dependencies-Zero%20(Pure%20Python)-brightgreen.svg)](https://github.com/adityaagrawal04/gramsort)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange.svg)](https://github.com/adityaagrawal04/gramsort/pulls)

*Transform messy, cryptic Instagram data exports into beautifully organized, captioned, and deduplicated libraries.*

[Features](#-key-features) • [Before & After](#-before--after) • [Quick Start](#-quick-start) • [How It Works](#-how-it-works) • [FAQ](#-frequently-asked-questions)

</div>

---

## 🧐 The Problem with Instagram Exports

When you download your data from Instagram or Meta Accounts Center, you receive gigabytes of chaotic, unorganized files:
- **Cryptic Filenames**: Media files are named with random numeric IDs (e.g. `18139097890568540.mp4`, `17872717830626145.webp`).
- **Scattered Across Months & Split Parts**: Multi-part zip downloads scatter your photos and videos across dozens of dated subfolders.
- **Rampant Duplicates**: Stories, feed posts, reels, and archived memories frequently duplicate the exact same photo or clip at different compression levels.
- **Disconnected Captions**: Your captions and timestamps are buried inside separate JSON or HTML metadata files.

**GramSort solves this completely in seconds.**

---

## 📁 Before & After

### Before GramSort
```text
instagram-export-2026/
├── part_1/
│   ├── media/
│   │   ├── posts/202110/18012629246708407.jpg
│   │   ├── reels/202608/18139097890568540.mp4
│   │   └── stories/202302/18024061750469097.jpg
│   └── your_instagram_activity/media/posts_1.html
├── part_2/
│   └── media/posts/202310/18264730594164112.jpg  <-- (duplicate!)
```

### After GramSort
```text
Organized_Media/
├── Reels/
│   ├── Never Travel with a special train #railway.mp4
│   ├── Never Travel with a special train #railway.srt   <-- (companion subtitle synced)
│   └── Bangkok Street Food Tour #thailand.mp4
├── Posts/
│   ├── Thailand it is.jpg                               <-- (single post)
│   └── Jai Jagannath Rath Yatra/                        <-- (carousel album post)
│       ├── Jai Jagannath Rath Yatra_1.webp
│       ├── Jai Jagannath Rath Yatra_2.webp
│       └── Jai Jagannath Rath Yatra_3.mp4
└── Stories/
    ├── Somnath Temple Darshan.webp
    └── 18024061750469097.jpg                            <-- (original ID if uncaptioned)
```

---

## ✨ Key Features

- 📂 **Three Clean Target Folders**:
  - `Reels/`: Flat folder containing all reel videos and companion `.srt` subtitles.
  - `Posts/`: Flat media for single posts; dedicated subfolders for multi-image/video carousels.
  - `Stories/`: Flat media for single stories; dedicated subfolders for multi-item stories.
- ⚡ **Zero-Dependency Resolution Inspection (No FFmpeg Needed)**:
  - Built-in pure-Python ISO BMFF header parser extracts video dimensions (`width` $\times$ `height`) directly from MP4/MOV track headers (`tkhd`).
  - Native binary header parsers for JPEG, PNG, WEBP, and GIF (Pillow optional, not required).
- 🧠 **Dual-Tier Quality Deduplication**:
  - Identifies cross-posted duplicate media across stories, posts, and archives using Instagram Media IDs and content hashing.
  - Compares candidate files by **Resolution first**, then by **File Size** — the higher-quality file wins, and the lower-quality duplicate is discarded.
- 🔍 **Universal Metadata Discovery**:
  - Handles both **JSON** exports (`reels.json`, `posts_1.json`, `stories.json`) and **HTML** exports (`reels.html`, `posts_1.html`, `posts.html`, `stories.html`).
  - Automatically joins multi-part split downloads (Part 1, Part 2, Part 3).
- 🪟 **Windows-Hardened Filename Sanitizer**:
  - Removes illegal characters (`\ / : * ? " < > |`) and control bytes.
  - Trims captions cleanly to ~80 characters without trailing dots or spaces.
  - Prevents collisions with Windows reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).
  - Appends numeric suffixes (`_1`, `_2`) if two separate posts share the exact same caption.
- 🔒 **100% Non-Destructive**:
  - Reads source archives safely without altering or deleting any original files.

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/adityaagrawal04/gramsort.git
cd gramsort
```

*(Optional)* Install Pillow if you want extended image codec support:
```bash
pip install -r requirements.txt
```

### 2. Preview with Dry Run (Safe Simulation)
Check how many files will be organized and how many duplicates will be resolved without writing any files:
```bash
python organize_media.py "C:\path\to\your\instagram-export" --dry-run
```

### 3. Organize Your Media
Execute the organization process:
```bash
python organize_media.py "C:\path\to\your\instagram-export"
```
By default, files are copied to an `Organized_Media` folder created directly beside your export.

### 4. Custom Output Directory
Specify an external drive or custom folder:
```bash
python organize_media.py "C:\path\to\instagram-export" --output-dir "D:\Photos\Instagram"
```

---

## 🛠️ Command-Line Options

| Flag | Shorthand | Description | Default |
|---|---|---|---|
| `export_dir` | *(positional)* | Path to the unzipped Instagram export folder | Current Directory |
| `--output-dir` | `-o` | Custom target directory for organized media | `Organized_Media` beside export |
| `--dry-run` | | Simulate execution and print statistics without writing files | `False` |
| `--verbose` | `-v` | Enable detailed debug logs for deep inspection | `False` |

---

## 📊 Example Output Report

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

## 🧪 Running Unit Tests

The repository includes a standalone test suite with no external testing dependencies:

```bash
python -m unittest discover tests
```

---

## 💡 Frequently Asked Questions

<details>
<summary><b>Does GramSort delete or alter my original Instagram export?</b></summary>
<p>No. GramSort operates strictly in a non-destructive manner. All organized files are copied into a separate <code>Organized_Media</code> folder using <code>shutil.copy2</code>, preserving original creation timestamps and file metadata.</p>
</details>

<details>
<summary><b>What if my Instagram export came in multiple ZIP parts?</b></summary>
<p>GramSort automatically scans subdirectories recursively. If you unzipped Part 1, Part 2, and Part 3 into one folder, GramSort indexes files across all parts and merges them into one unified structure.</p>
</details>

<details>
<summary><b>Do I need ffmpeg or ffprobe installed?</b></summary>
<p>No! GramSort has a built-in ISO BMFF parser written in pure Python that reads MP4/MOV track header boxes directly from binary streams to extract width and height in milliseconds.</p>
</details>

<details>
<summary><b>What file formats are supported?</b></summary>
<p>Images: <code>.jpg</code>, <code>.jpeg</code>, <code>.png</code>, <code>.webp</code>, <code>.heic</code><br>
Videos: <code>.mp4</code>, <code>.mov</code>, <code>.m4v</code><br>
Subtitles: <code>.srt</code>, <code>.vtt</code></p>
</details>

---

## 🤝 Contributing

Contributions, bug reports, and feature suggestions are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AwesomeFeature`)
3. Commit your Changes (`git commit -m 'Add some AwesomeFeature'`)
4. Push to the Branch (`git push origin feature/AwesomeFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
