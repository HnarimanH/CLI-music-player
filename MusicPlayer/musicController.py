import audioEngine as Audio
import os

from functions.filterFormats import filterFormats
from library import get_song_info
songs_dir = "/Users/narimanhosseinzadeh/Documents/music/"

songs = filterFormats(songs_dir)

os.system("cls" if os.name == "nt" else "clear")

    
    
def return_library():
    song_list = []

    for song in songs:
        path = os.path.join(songs_dir, song)
        info = get_song_info(path)

        song_list.append({
            "title": info["title"],
            "artist": info["artist"],
            "album": info["album"],
            "length": info["length"],
            "cover": info["cover"],
            "filename": song,
            "path": path,
        })
    return song_list
        
    
    
def play_song(index):
    if index < 1 or index > len(songs):
        print("Invalid song number")
        return
    selected_song = os.path.join(songs_dir, songs[index - 1])
    Audio.play_song(selected_song)
def pause_song():
    Audio.pause_song()
def unpause_song():
    Audio.unpause_song()
def stop_song():
    Audio.stop_song()