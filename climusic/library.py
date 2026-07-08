from mutagen import File
from mutagen.mp4 import MP4Cover
from importlib import resources


def get_song_info(path):
    try:
        audio = File(path, easy=False)  # easy=False to get cover art

        if audio is None or not hasattr(audio, "info"):
            return None

    except Exception as e:
        print(f"Skipping {path}: {e}")
        return None

    with resources.files("climusic.assets").joinpath("defaultAlbumCover.jpeg").open("rb") as f:
        cover_data = f.read()

    try:
        tags = audio.tags
        title = artist = album = None

        if tags is None:
            pass
        elif hasattr(audio, "tags") and audio.__class__.__name__ in ("MP3", "FLAC", "OGG"):
            # ID3 tags (mp3)
            from mutagen.id3 import ID3NoHeaderError
            t = tags.get("TIT2"); title = t.text[0] if t else None
            a = tags.get("TPE1"); artist = a.text[0] if a else None
            al = tags.get("TALB"); album = al.text[0] if al else None
            for tag in tags.values():
                if hasattr(tag, "FrameID") and tag.FrameID == "APIC":
                    cover_data = tag.data
                    break
        else:
            # MP4/M4A/WebM tags
            title = tags.get("\xa9nam", [None])[0]
            artist = tags.get("\xa9ART", [None])[0]
            album = tags.get("\xa9alb", [None])[0]
            covr = tags.get("covr")
            if covr:
                cover_data = bytes(covr[0])

    except Exception as e:
        print(f"tag error {path}: {e}")

    length_seconds = int(audio.info.length)

    return {
        "title": title or "Unknown Title",
        "artist": artist or "Unknown Artist",
        "album": album or "Unknown Album",
        "length": f"{length_seconds // 60}:{length_seconds % 60:02d}",
        "cover": cover_data
    }