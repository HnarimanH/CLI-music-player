from mutagen import File
from mutagen.id3 import ID3, ID3NoHeaderError

def get_song_info(path):
    try:
        audio = File(path, easy=True)

        if audio is None or not hasattr(audio, "info"):
            return None

    except Exception as e:
        print(f"Skipping {path}: {e}")
        return None

    with open("assets/defaultAlbumCover.jpeg", "rb") as f:
        cover_data = f.read()

    try:
        tags = ID3(path)

        title = tags.get("TIT2")
        artist = tags.get("TPE1")
        album = tags.get("TALB")

        for tag in tags.values():
            if tag.FrameID == "APIC":
                cover_data = tag.data
                break

    except ID3NoHeaderError:
        title = artist = album = None

    length_seconds = int(audio.info.length)

    return {
        "title": title.text[0] if title else "Unknown Title",
        "artist": artist.text[0] if artist else "Unknown Artist",
        "album": album.text[0] if album else "Unknown Album",
        "length": f"{length_seconds // 60}:{length_seconds % 60:02d}",
        "cover": cover_data
    }