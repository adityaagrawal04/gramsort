# Instagram Media Organizer

A robust, dependency-light Python automation tool to organize Instagram and Facebook data exports on Windows, macOS, and Linux.

It sorts your photos, videos, reels, and stories into clean top-level folders, groups multi-item posts (carousels/albums) into dedicated subfolders, sanitizes filenames using post captions, and automatically resolves duplicate media keeping only the highest-quality version.

---

## Features

- **Three Dedicated Top-Level Folders**:
  - `Reels/`: Flat folder containing all reel video files and companion `.srt` subtitles.
  - `Posts/`: Flat media for single posts; dedicated subfolders for multi-image/video carousels.
  - `Stories/`: Flat media for single stories; dedicated subfolders for multi-item stories.
- **Smart Discovery (JSON & HTML)**:
  - Dynamically searches for Instagram metadata across single or multi-part split exports.
  - Supports both standard JSON exports (`reels.json`, `posts_1.json`, etc.) and HTML exports (`reels.html`, `posts_1.html`, etc.).
  - Accurately associates unreferenced media based on directory context.
- **Caption-Based Renaming**:
  - Extracts titles and captions, fixes Instagram Latin-1/UTF-8 mojibake, unescapes HTML entities, and trims to ~80 characters.
  - Strips illegal Windows filename characters (`\ / : * ? " < > |`) and avoids reserved device names (`CON`, `PRN`, `AUX`, `NUL`, etc.).
  - Appends numeric suffixes (`_1`, `_2`, etc.) to prevent collisions when different posts share the same caption.
  - Falls back to the original export filename if no caption exists.
- **Quality-Based Deduplication**:
  - Compares duplicates by **resolution (width × height) first, then by file size**.
  - Identifies cross-posted media across stories, posts, and archives using Instagram Media IDs and content hashing.
  - Retains the larger, higher-resolution copy and discards lower-quality duplicates.
- **FFmpeg-Free Metadata Reading**:
  - Pure-Python ISO BMFF header parser extracts MP4/MOV video dimensions without requiring `ffmpeg` or `ffprobe`.
  - Uses Pillow when installed, with a pure-Python binary header parser fallback for JPEG, PNG, WEBP, and GIF images.
- **Non-Destructive**:
  - Reads source files safely and copies them to `Organized_Media` without modifying or deleting files in the original export.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/adityaagrawal04/instagram-media-organizer.git
cd instagram-media-organizer
```

*(Optional)* Install Pillow for expanded image format support:

```bash
pip install -r requirements.txt
```

---

## Usage

### 1. Preview with Dry Run (Safe Simulation)
Simulate the run and view statistics without copying any files:

```bash
python organize_media.py "C:\path\to\instagram-export" --dry-run
```

### 2. Organize Media
Run the organization process:

```bash
python organize_media.py "C:\path\to\instagram-export"
```
By default, the organized files will be placed in an `Organized_Media` folder created beside your export folder.

### 3. Specify Custom Output Directory

```bash
python organize_media.py "C:\path\to\instagram-export" --output-dir "D:\My_Photos"
```

### Command Line Options

| Option | Description |
|---|---|
| `export_dir` | Path to the unzipped Instagram export folder |
| `--output-dir`, `-o` | Custom destination directory for organized media |
| `--dry-run` | Simulate the process without copying files to disk |
| `--verbose`, `-v` | Enable detailed debug logging |

---

## Running Tests

Run the built-in unit tests using Python's standard `unittest` framework:

```bash
python -m unittest discover tests
```
