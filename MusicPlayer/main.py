from library import get_song_info
from player import play_song
import os
from functions.filterFormats import filterFormats
os.system("cls" if os.name == "nt" else "clear")
songs_dir = "/Users/narimanhosseinzadeh/Documents/music/"

songs = filterFormats(songs_dir)
        
os.system("cls" if os.name == "nt" else "clear")
for i, song in enumerate(songs):
    path = os.path.join(songs_dir, song)
    info = get_song_info(path)
    print(f"{i+1}. {info['title']} - {info['artist']} - {info['length']}")
   

choice = int(input("Choose a song: "))

selected_song = songs[choice - 1]

play_song(os.path.join(songs_dir, selected_song))
