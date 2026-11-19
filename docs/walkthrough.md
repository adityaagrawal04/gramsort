# Engineering Walkthrough: Building GramSort

**Subtitle**: How to organize, caption, and deduplicate 7,000+ files from an unzipped Instagram export in pure Python without external dependencies.

---

## 1. The Challenge of Social Media Takeout

When exporting personal archives from Meta or Instagram Accounts Center, users typically expect neat chronological photo albums. Instead, the download contains:

1. Cryptic IDs as filenames (`18139097890568540.mp4`, `17872717830626145.webp`).
2. Data partitioned into dozens of dated folders (`202110/`, `202305/`) and split archive parts.
3. Content duplicated between feeds, stories, and memory highlights.
4. Text captions stored separately in JSON or HTML metadata tables.

---

## 2. Reading Video Dimensions without FFmpeg

Determining video resolutions usually relies on `ffprobe` or `OpenCV`. However, spawning external subprocesses thousands of times introduces significant execution overhead and requires users to install non-Python tools.

GramSort implements a pure-Python ISO Base Media File Format (ISO BMFF) parser:
- Reads the file's binary stream directly.
- Scans top-level atoms to locate the `moov` container box.
- Walks through each `trak` (track) child box.
- Inspects the `tkhd` (track header) atom to decode the 16.16 fixed-point display resolution integers in under a millisecond per file.

---

## 3. Two-Tier Deduplication Strategy

Cross-posted items across Instagram stories and feed posts often have identical media content with different filenames or recompression levels.

GramSort uses a two-tier approach:
1. **Instagram Media ID Matching**: Parses the underlying numeric token from filenames to match identical uploads.
2. **Lazy SHA-256 Checksums**: Content hashes are only calculated when two files share the exact same byte size, avoiding disk reads on unique files.
3. **Quality Ranking**: The winner is selected using:
   $$\text{Quality Score} = (\text{Width} \times \text{Height}, \text{File Size})$$
   Preserving the highest resolution copy.

---

## 4. Recovering Latin-1 Mojibake

Meta's export tools historically decode certain UTF-8 strings (such as emojis or accented text) through ISO-8859-1 (Latin-1), producing garbled text. 

GramSort restores these automatically:
```python
def fix_mojibake(text: str) -> str:
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
```

---

## 5. Summary & Repository

GramSort is available under the MIT license on GitHub:  
https://github.com/adityaagrawal04/gramsort
