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
    cover_data = get_song_info(song["path"])["cover"]
    ascii_cover = cover_to_ascii(cover_data, width=72)
    
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













PLAYLISTS_FILE = "playlists.json"



def get_playlists():
    """Load all playlists"""
    if not os.path.exists(PLAYLISTS_FILE):
        return {}
    with open(PLAYLISTS_FILE, "r") as f:
        return json.load(f)

def save_playlists(playlists):
    """Save playlists"""
    with open(PLAYLISTS_FILE, "w") as f:
        json.dump(playlists, f, indent=2)

def create_playlist(name):
    """Create new playlist"""
    playlists = get_playlists()
    if name in playlists:
        return False  # already exists
    playlists[name] = []
    save_playlists(playlists)
    return True

def add_to_playlist(playlist_name, song):
    """Add song to playlist"""
    playlists = get_playlists()
    if playlist_name not in playlists:
        return False
    playlists[playlist_name].append(song)
    save_playlists(playlists)
    return True

def load_playlist(playlist_name):
    """Get songs from playlist"""
    playlists = get_playlists()
    return playlists.get(playlist_name, [])

def delete_playlist(playlist_name):
    """Delete entire playlist"""
    playlists = get_playlists()
    if playlist_name in playlists:
        del playlists[playlist_name]
        save_playlists(playlists)
        return True
    return False