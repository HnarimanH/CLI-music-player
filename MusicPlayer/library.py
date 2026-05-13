from mutagen import File
from mutagen.id3 import ID3, ID3NoHeaderError

def get_song_info(path):
    audio = File(path, easy=True)

    try:
        tags = ID3(path)
        title = tags.get("TIT2")
        artist = tags.get("TPE1")
        album = tags.get("TALB")
    except ID3NoHeaderError:
        title = artist = album = None
    length_seconds = int(audio.info.length)
    minutes = length_seconds // 60
    seconds = length_seconds % 60
    formatted_length = f"{minutes}:{seconds:02d}"
    return {
        "title": title.text[0] if title else "Unknown Title",
        "artist": artist.text[0] if artist else "Unknown Artist",
        "album": album.text[0] if album else "Unknown Album",
        "length": formatted_length
    }
