import audioEngine as Audio
import os
from functions.filterFormats import filterFormats
from library import get_song_info
from functions.coverToAscii import cover_to_ascii
from functions.extractAudioWave import get_audio_wave
import json
import random
songs_dir = ""

while True:
    if not os.path.exists("config.json"):

        directory = input("Please enter your music directory path: ")

        if os.path.isdir(directory):

            with open("config.json", "w") as f:
                json.dump({"dir": directory,"theme": "black","visualizer":True,"shuffle": False, "repeat": False}, f)

            songs_dir = directory
            break

        else:
            print("Invalid directory")

    else:

        with open("config.json", "r") as f:
            data = json.load(f)

        songs_dir = data["dir"]
        break



songs = filterFormats(songs_dir)


    
    
def return_library():
    song_list = []

    for song in songs:
        if song.startswith("._") and os.name == 'nt':
            os.remove(os.path.join(songs_dir, song))
            continue
            
        path = os.path.join(songs_dir, song)

        info = get_song_info(path)

        if info is None:
            print(f"Skipping invalid file: {path}")
            continue

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
        
def shuffle_library(library):
    shuffled = library.copy()  # don't modify original
    random.shuffle(shuffled)
    return shuffled
def play_song(song_data):
    """Play a song using its data dict"""
    if not song_data or "path" not in song_data:
        print("Invalid song data")
        return
    Audio.play_song(song_data["path"])
def pause_song():
    Audio.pause_song()
def unpause_song():
    Audio.unpause_song()
def stop_song():
    Audio.stop_song()
def set_volume(level):
    Audio.set_volume(level)
def get_volume():
    return Audio.get_volume()

def load_song(index, songs):
    song = songs[index]
    ascii_cover = cover_to_ascii(song["cover"], width=72)
    
    with open("config.json", "r") as f:
        config = json.load(f)
    
    visualizer_frames = []
    if config.get("visualizer", True):
        visualizer_frames = get_audio_wave(song["path"])
    
    return {
        "song": song,
        "ascii_cover": ascii_cover,
        "visualizer_frames": visualizer_frames,  # always return it (empty list if off)
    }