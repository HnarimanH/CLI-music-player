import re
import bisect
from typing import Dict, List, Optional, Tuple, Any

# Matches standard timestamp [mm:ss.xx] or [mm:ss.xxx] or [mm:ss]
TIME_TAG_REGEX = re.compile(r'\[(\d+):(\d{2})(?:\.(\d+))?\]')
# Matches [offset:+/-ms]
OFFSET_TAG_REGEX = re.compile(r'\[offset:\s*([+-]?\d+)\s*\]', re.IGNORECASE)
# Matches word-level enhanced LRC tags like <00:12.34>
ENHANCED_TAG_REGEX = re.compile(r'<\d+:\d+(?:\.\d+)?>')
# Matches metadata tags like [ti:Title], [ar:Artist], etc.
METADATA_TAG_REGEX = re.compile(r'\[(ti|ar|al|by|length|re|ve|offset):.*?\]', re.IGNORECASE)

# Patterns for cleaning noisy titles from YouTube / downloads
CLEANUP_PATTERNS = [
    re.compile(r'\s*[\(\[](?:official\s+)?(?:music\s+)?(?:video|audio|lyric\s+video|lyrics?|visualizer)[\)\]]', re.IGNORECASE),
    re.compile(r'\s*[\(\[](?:4k|hd|hq|remaster(?:ed)?(?:\s+\d+)?|\d{4}\s+remaster(?:ed)?|explicit|audio|mono|stereo)[\)\]]', re.IGNORECASE),
    re.compile(r'\s*[\(\[](?:prod\.|produced\s+by).*?[\)\]]', re.IGNORECASE),
    re.compile(r'\s*[\(\[]ft\.?|feat\.?.*?[\)\]]', re.IGNORECASE),
    re.compile(r'^\d+[\s\.\-_]+'),  # Leading track numbers like "01 - " or "01. "
]


def clean_title_and_artist(title: Optional[str], artist: Optional[str], filename: Optional[str] = None) -> Tuple[str, str]:
    """
    Cleans up title and artist strings by removing common video tags, track numbers,
    splitting 'Artist - Title' if packed in title or filename, and normalizing suffixes like '- Topic'.
    """
    clean_title = (title or "").strip()
    clean_artist = (artist or "").strip()

    # Strip YouTube channel suffix like "Coldplay - Topic"
    if clean_artist.lower().endswith(" - topic"):
        clean_artist = clean_artist[:-8].strip()

    # If title is unknown, generic, or empty, attempt extraction from filename
    if not clean_title or clean_title.lower() in ("unknown title", "unknown", "track 01", "untitled"):
        if filename:
            base = re.sub(r'\.[a-zA-Z0-9]+$', '', filename).strip()
            if " - " in base:
                parts = base.split(" - ", 1)
                if not clean_artist or clean_artist.lower() in ("unknown artist", "unknown", "youtube"):
                    clean_artist = parts[0].strip()
                clean_title = parts[1].strip()
            else:
                clean_title = base

    # If artist is missing or generic, but title contains "Artist - Song"
    if (not clean_artist or clean_artist.lower() in ("unknown artist", "unknown", "youtube")) and " - " in clean_title:
        parts = clean_title.split(" - ", 1)
        clean_artist = parts[0].strip()
        clean_title = parts[1].strip()

    # Clean title noise
    for pat in CLEANUP_PATTERNS:
        clean_title = pat.sub('', clean_title)
    clean_title = clean_title.strip()

    # Clean artist noise
    if clean_artist and clean_artist.lower() in ("unknown artist", "unknown", "youtube"):
        clean_artist = ""
    else:
        for pat in CLEANUP_PATTERNS:
            clean_artist = pat.sub('', clean_artist)
        clean_artist = clean_artist.strip()

    return clean_title or "Unknown Title", clean_artist or "Unknown Artist"


def parse_lrc(lrc_text: str, extra_offset_ms: int = 0) -> Dict[str, Any]:
    """
    Parses LRC content or plain text lyrics.
    Supports multiple timestamps per line, offset headers, and unsynchronized text.
    """
    if not lrc_text or not lrc_text.strip():
        return {
            "synced": False,
            "lines": [],
            "offset_ms": 0,
            "raw": ""
        }

    offset_ms = 0
    for line in lrc_text.splitlines():
        off_match = OFFSET_TAG_REGEX.match(line.strip())
        if off_match:
            try:
                offset_ms = int(off_match.group(1))
            except ValueError:
                offset_ms = 0
            break

    total_offset_ms = offset_ms + extra_offset_ms
    parsed_lines: List[Dict[str, Any]] = []
    has_timestamps = False

    for line in lrc_text.splitlines():
        line_str = line.strip()
        if not line_str:
            continue

        # Check if line is purely metadata (like [ar:Coldplay])
        if METADATA_TAG_REGEX.fullmatch(line_str):
            continue

        tags = TIME_TAG_REGEX.findall(line_str)
        if tags:
            has_timestamps = True
            # Strip time tags and enhanced tags from text
            text = TIME_TAG_REGEX.sub('', line_str).strip()
            text = ENHANCED_TAG_REGEX.sub('', text).strip()

            for m, s, frac in tags:
                sec = int(m) * 60 + int(s)
                if frac:
                    sec += int(frac) / (10 ** len(frac))
                sec += total_offset_ms / 1000.0
                parsed_lines.append({
                    "time": max(0.0, sec),
                    "text": text
                })

    if has_timestamps and parsed_lines:
        parsed_lines.sort(key=lambda x: x["time"])
        return {
            "synced": True,
            "lines": parsed_lines,
            "offset_ms": total_offset_ms,
            "raw": lrc_text
        }
    else:
        # Fallback: Plain unsynchronized lyrics
        plain_lines = []
        for line in lrc_text.splitlines():
            # Skip metadata lines if any
            if METADATA_TAG_REGEX.fullmatch(line.strip()):
                continue
            clean_l = line.strip()
            if clean_l:
                plain_lines.append({
                    "time": None,
                    "text": clean_l
                })
        return {
            "synced": False,
            "lines": plain_lines,
            "offset_ms": total_offset_ms,
            "raw": lrc_text
        }


def get_active_line_index(lines: List[Dict[str, Any]], current_time: float, is_synced: bool = True) -> int:
    """
    Returns the 0-based index of the currently active lyric line for the given timestamp.
    Returns -1 if before the first line or if lines are empty/unsynced.
    """
    if not lines or not is_synced:
        return -1

    if current_time < lines[0]["time"]:
        return -1

    # Extract all timestamps for binary search
    times = [item["time"] for item in lines]
    idx = bisect.bisect_right(times, current_time) - 1
    return max(0, min(idx, len(lines) - 1))


def format_time(seconds: Optional[float]) -> str:
    """Formats float seconds into mm:ss format."""
    if seconds is None or seconds < 0:
        return "--:--"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"
