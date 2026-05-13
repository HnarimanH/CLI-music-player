
import os


supported_formats = (".mp3", ".wav", ".ogg")
def filterFormats(songs_dir):
    allFiles = os.listdir(songs_dir)
    songs= []
    for file in allFiles:
        if file.lower().endswith(supported_formats):
            songs.append(file)
    return songs