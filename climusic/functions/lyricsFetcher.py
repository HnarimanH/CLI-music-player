import os
import re
import json
import urllib.request
import urllib.parse
import difflib
from pathlib import Path
from typing import Optional, Dict, Any, List
from mutagen import File

from climusic.musicController import APP_DIR
from climusic.functions.lyricsParser import parse_lrc, clean_title_and_artist

LYRICS_DIR = APP_DIR / "lyrics"
LYRICS_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "CLPYmusic/0.1.7 (https://github.com/HnarimanH/CLI-music-player)"
LRCLIB_GET_URL = "https://lrclib.net/api/get"
LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"


def sanitize_filename(name: str) -> str:
    """Removes invalid filesystem characters for caching."""
    return re.sub(r'[\\/*?:"<>|]', '_', name).strip()


def get_local_file_lyrics(song_path: str) -> Optional[Dict[str, Any]]:
    """Checks for .lrc or .txt in the same directory as the song file."""
    try:
        base_path = os.path.splitext(song_path)[0]
        for ext in ('.lrc', '.txt'):
            target = base_path + ext
            if os.path.isfile(target):
                with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                if content:
                    return {
                        "source": "local_file",
                        "path": target,
                        "content": content
                    }
    except Exception:
        pass
    return None


def get_cached_lyrics(title: str, artist: str, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Checks ~/.climusic/lyrics/ for cached .lrc files."""
    clean_t, clean_a = clean_title_and_artist(title, artist, filename)
    candidates = []

    if clean_a and clean_t:
        candidates.append(f"{sanitize_filename(clean_a)} - {sanitize_filename(clean_t)}.lrc")
    if clean_t:
        candidates.append(f"{sanitize_filename(clean_t)}.lrc")
    if filename:
        base_file = os.path.splitext(os.path.basename(filename))[0]
        candidates.append(f"{sanitize_filename(base_file)}.lrc")

    for cand in candidates:
        target = LYRICS_DIR / cand
        if target.is_file():
            try:
                with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                if content:
                    return {
                        "source": "cache",
                        "path": str(target),
                        "content": content
                    }
            except Exception:
                pass
    return None


def get_embedded_lyrics(song_path: str) -> Optional[Dict[str, Any]]:
    """Extracts embedded lyrics from audio metadata (ID3 USLT/SYLT, MP4, Vorbis)."""
    try:
        audio = File(song_path, easy=False)
        if audio is None or not hasattr(audio, "tags") or not audio.tags:
            return None

        tags = audio.tags

        # 1. ID3 (MP3)
        if hasattr(tags, "getall"):
            # Check for SYLT (Synchronized Lyrics)
            sylt_frames = tags.getall("SYLT")
            for sylt in sylt_frames:
                if hasattr(sylt, "text") and sylt.text:
                    # Convert SYLT [(text, ms), ...] to standard LRC format
                    lines = []
                    for item in sylt.text:
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            t_text, t_ms = item[0], item[1]
                            total_s = t_ms / 1000.0
                            m = int(total_s // 60)
                            s = int(total_s % 60)
                            cs = int((total_s - int(total_s)) * 100)
                            lines.append(f"[{m:02d}:{s:02d}.{cs:02d}]{t_text}")
                    if lines:
                        return {
                            "source": "embedded (SYLT)",
                            "content": "\n".join(lines)
                        }

            # Check for USLT (Unsynchronized Lyrics)
            uslt_frames = tags.getall("USLT")
            for uslt in uslt_frames:
                if hasattr(uslt, "text") and uslt.text.strip():
                    return {
                        "source": "embedded (USLT)",
                        "content": uslt.text.strip()
                    }

        # 2. MP4 / M4A (atom \xa9lyr)
        if "\xa9lyr" in tags:
            lyr = tags["\xa9lyr"]
            if isinstance(lyr, list) and lyr and lyr[0].strip():
                return {
                    "source": "embedded (MP4)",
                    "content": lyr[0].strip()
                }

        # 3. Vorbis / FLAC / OGG
        for key in ("LYRICS", "lyrics", "UNSYNCEDLYRICS", "unsyncedlyrics"):
            if key in tags:
                val = tags[key]
                if isinstance(val, list) and val and val[0].strip():
                    return {
                        "source": "embedded (Vorbis)",
                        "content": val[0].strip()
                    }
                elif isinstance(val, str) and val.strip():
                    return {
                        "source": "embedded (Vorbis)",
                        "content": val.strip()
                    }

    except Exception:
        pass

    return None


def normalize_match_str(text: str) -> str:
    """Normalizes string for fuzzy comparison by lowercasing and stripping punctuation."""
    if not text:
        return ""
    return re.sub(r'[^\w\s]', '', text.lower()).strip()


def compute_lyrics_relevance(
    candidate: Dict[str, Any],
    target_title: str,
    target_artist: str,
    target_duration: Optional[float] = None
) -> float:
    """
    Computes a composite relevance score (0.0 to 1.0) between an LRCLIB candidate
    and the playing song based on artist, track title, duration proximity, and sync status.
    """
    c_title = candidate.get("trackName") or candidate.get("name") or ""
    c_artist = candidate.get("artistName") or ""
    c_dur = candidate.get("duration") or 0
    has_synced = bool(candidate.get("syncedLyrics"))
    has_plain = bool(candidate.get("plainLyrics"))
    is_inst = candidate.get("instrumental", False)

    # Disqualify candidates with no lyrics content
    if not has_synced and not has_plain and not is_inst:
        return 0.0

    norm_t_title = normalize_match_str(target_title)
    norm_c_title = normalize_match_str(c_title)
    norm_t_artist = normalize_match_str(target_artist)
    norm_c_artist = normalize_match_str(c_artist)

    # 1. Title Similarity (Weight: 40%)
    if norm_t_title == norm_c_title:
        title_score = 1.0
    elif norm_t_title and norm_c_title and (norm_t_title in norm_c_title or norm_c_title in norm_t_title):
        title_score = 0.90
    else:
        title_score = difflib.SequenceMatcher(None, norm_t_title, norm_c_title).ratio()

    # 2. Artist Similarity (Weight: 35%)
    if not norm_t_artist or norm_t_artist in ("unknown artist", "unknown", "youtube"):
        artist_score = 0.70  # Neutral when artist is unspecified
    elif norm_t_artist == norm_c_artist:
        artist_score = 1.0
    elif norm_t_artist in norm_c_artist or norm_c_artist in norm_t_artist:
        artist_score = 0.92
    else:
        artist_score = difflib.SequenceMatcher(None, norm_t_artist, norm_c_artist).ratio()

    # Penalize heavily if artist was known but candidate artist is completely different (< 0.35)
    if norm_t_artist and norm_t_artist not in ("unknown artist", "unknown", "youtube"):
        if artist_score < 0.35:
            return 0.05

    # 3. Duration Proximity (Weight: 15%)
    if target_duration and target_duration > 0 and c_dur and c_dur > 0:
        diff = abs(target_duration - c_dur)
        if diff <= 3:
            dur_score = 1.0
        elif diff <= 10:
            dur_score = 0.85
        elif diff <= 25:
            dur_score = 0.65
        elif diff <= 45:
            dur_score = 0.40
        else:
            dur_score = 0.15
    else:
        dur_score = 0.70

    # 4. Synchronized Bonus (Weight: 10%)
    synced_score = 1.0 if has_synced else 0.55

    score = (artist_score * 0.35) + (title_score * 0.40) + (dur_score * 0.15) + (synced_score * 0.10)
    return score


def fetch_most_relative_online_lyrics(
    title: str,
    artist: str,
    album: Optional[str] = None,
    duration: Optional[float] = None,
    filename: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Searches LRCLIB using multiple candidate strategies, scores all results
    to select the most relevant lyrics based on artist, track name, and duration,
    and automatically saves the selected match to cache.
    """
    clean_t, clean_a = clean_title_and_artist(title, artist, filename)
    if not clean_t:
        return None

    candidates_by_id: Dict[Any, Dict[str, Any]] = {}

    def add_candidates_from_url(url: str):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    items = json.loads(response.read().decode("utf-8"))
                    if isinstance(items, list):
                        for it in items:
                            cid = it.get("id") or (it.get("trackName"), it.get("artistName"))
                            if cid not in candidates_by_id:
                                candidates_by_id[cid] = it
                    elif isinstance(items, dict) and items.get("id"):
                        cid = items.get("id")
                        if cid not in candidates_by_id:
                            candidates_by_id[cid] = items
        except Exception:
            pass

    # Strategy 1: Targeted track_name and artist_name search
    if clean_a and clean_a != "Unknown Artist":
        p1 = {"track_name": clean_t, "artist_name": clean_a}
        add_candidates_from_url(f"{LRCLIB_SEARCH_URL}?{urllib.parse.urlencode(p1)}")

    # Strategy 2: Combined full-text query "Artist Title"
    q_str = f"{clean_a} {clean_t}".strip() if clean_a and clean_a != "Unknown Artist" else clean_t
    add_candidates_from_url(f"{LRCLIB_SEARCH_URL}?{urllib.parse.urlencode({'q': q_str})}")

    # Strategy 3: If few candidates, query by title alone
    if len(candidates_by_id) < 3:
        add_candidates_from_url(f"{LRCLIB_SEARCH_URL}?{urllib.parse.urlencode({'q': clean_t})}")

    if not candidates_by_id:
        return None

    # Score all candidates for relevance
    scored_candidates = []
    for it in candidates_by_id.values():
        score = compute_lyrics_relevance(it, clean_t, clean_a, duration)
        scored_candidates.append((score, it))

    # Sort descending by relevance score
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best_match = scored_candidates[0]

    # Threshold: must have a solid match score (>= 0.45)
    if best_score < 0.45:
        return None

    content = best_match.get("syncedLyrics") or best_match.get("plainLyrics")
    if best_match.get("instrumental") and not content:
        content = "[00:00.00] ♪ Instrumental ♪"

    if not content:
        return None

    # Automatically save the most relative lyrics to disk cache
    save_lyrics_to_cache(clean_t, clean_a, content, filename=filename)

    matched_t = best_match.get("trackName") or clean_t
    matched_a = best_match.get("artistName") or clean_a
    match_pct = int(best_score * 100)

    return {
        "source": f"online (LRCLIB • {match_pct}% match)",
        "source_type": "online",
        "instrumental": best_match.get("instrumental", False),
        "content": content,
        "score": best_score,
        "matched_title": matched_t,
        "matched_artist": matched_a,
    }


def search_lrclib(query: str, target_artist: Optional[str] = None) -> List[Dict[str, Any]]:
    """Searches LRCLIB for a query and returns candidate results sorted by relevance."""
    try:
        url = f"{LRCLIB_SEARCH_URL}?{urllib.parse.urlencode({'q': query})}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                results = []
                for item in data[:8]:
                    results.append({
                        "id": item.get("id"),
                        "title": item.get("trackName") or item.get("name") or "Unknown",
                        "artist": item.get("artistName") or "Unknown",
                        "album": item.get("albumName") or "",
                        "duration": item.get("duration"),
                        "synced": bool(item.get("syncedLyrics")),
                        "instrumental": item.get("instrumental", False),
                        "content": item.get("syncedLyrics") or item.get("plainLyrics") or ""
                    })

                # Sort search results by relevance to query if applicable
                if results:
                    results.sort(
                        key=lambda x: compute_lyrics_relevance(x, query, target_artist or ""),
                        reverse=True
                    )
                return results[:5]
    except Exception:
        pass
    return []


def save_lyrics_to_cache(title: str, artist: str, content: str, filename: Optional[str] = None) -> Optional[str]:
    """
    Saves lyrics to ~/.climusic/lyrics/<artist> - <title>.lrc
    and optionally by song filename for instant local lookups.
    """
    try:
        clean_t, clean_a = clean_title_and_artist(title, artist, filename)
        fname = f"{sanitize_filename(clean_a)} - {sanitize_filename(clean_t)}.lrc"
        out_path = LYRICS_DIR / fname
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Also cache under clean title if artist was unknown
        if not clean_a or clean_a == "Unknown Artist":
            alt_path = LYRICS_DIR / f"{sanitize_filename(clean_t)}.lrc"
            if alt_path != out_path:
                try:
                    with open(alt_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                except Exception:
                    pass

        # Also cache by song filename so exact file lookups are instant
        if filename:
            base_f = os.path.splitext(os.path.basename(filename))[0]
            f_path = LYRICS_DIR / f"{sanitize_filename(base_f)}.lrc"
            if f_path != out_path:
                try:
                    with open(f_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                except Exception:
                    pass

        return str(out_path)
    except Exception:
        return None


def load_lyrics_for_song(song: Dict[str, Any], allow_network: bool = True, extra_offset_ms: int = 0) -> Optional[Dict[str, Any]]:
    """
    Unified loader: Checks local file -> cache -> embedded -> online LRCLIB relative search.
    Returns parsed lyrics dictionary with metadata.
    """
    song_path = song.get("path", "")
    title = song.get("title", "")
    artist = song.get("artist", "")
    filename = song.get("filename", "")

    # Extract duration in seconds if length string is available
    duration: Optional[float] = None
    if "length" in song and song["length"]:
        l_str = str(song["length"])
        if ":" in l_str:
            parts = l_str.split(":")
            try:
                duration = float(int(parts[0]) * 60 + int(parts[1]))
            except (ValueError, IndexError):
                duration = None

    # 1. Local file alongside song (.lrc or .txt)
    res = get_local_file_lyrics(song_path)
    if res:
        parsed = parse_lrc(res["content"], extra_offset_ms=extra_offset_ms)
        parsed["source"] = "local (.lrc/.txt)"
        parsed["source_type"] = "local"
        parsed["path"] = res.get("path")
        return parsed

    # 2. Local cache in ~/.climusic/lyrics/
    res = get_cached_lyrics(title, artist, filename)
    if res:
        parsed = parse_lrc(res["content"], extra_offset_ms=extra_offset_ms)
        parsed["source"] = "cache (~/.climusic/lyrics)"
        parsed["source_type"] = "cache"
        parsed["path"] = res.get("path")
        return parsed

    # 3. Embedded audio tags (ID3 SYLT/USLT, MP4, Vorbis)
    res = get_embedded_lyrics(song_path)
    if res:
        parsed = parse_lrc(res["content"], extra_offset_ms=extra_offset_ms)
        parsed["source"] = f"embedded ({res['source']})"
        parsed["source_type"] = "embedded"
        return parsed

    # 4. Search and select/save the most relative online lyrics from LRCLIB
    if allow_network:
        res = fetch_most_relative_online_lyrics(
            title,
            artist,
            album=song.get("album"),
            duration=duration,
            filename=filename
        )
        if res and res.get("content"):
            parsed = parse_lrc(res["content"], extra_offset_ms=extra_offset_ms)
            parsed["source"] = res.get("source", "online (LRCLIB)")
            parsed["source_type"] = "online"
            parsed["instrumental"] = res.get("instrumental", False)
            parsed["score"] = res.get("score")
            parsed["matched_title"] = res.get("matched_title")
            parsed["matched_artist"] = res.get("matched_artist")
            return parsed

    return None
