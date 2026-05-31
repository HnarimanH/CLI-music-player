import audioEngine as Audio
import os

from functions.filterFormats import filterFormats
from library import get_song_info
songs_dir = "/Users/narimanhosseinzadeh/Documents/music/"

songs = filterFormats(songs_dir)

os.system("cls" if os.name == "nt" else "clear")

    
    
def show_library():
    for i, song in enumerate(songs):
        path = os.path.join(songs_dir, song)
        info = get_song_info(path)
        print(f"{i+1}. {info['title']} - {info['artist']} - {info['length']}")
        
        
    
    
def play_song(index):
    if index < 1 or index > len(songs):
        print("Invalid song number")
        return

    selected_song = os.path.join(songs_dir, songs[index - 1])

    print(f"\n▶ Playing: {selected_song}")
    Audio.play_song(selected_song)
def pause_song():
    Audio.pause_song()
def unpause_song():
    Audio.unpause_song()
def stop_song():
    Audio.stop_song()