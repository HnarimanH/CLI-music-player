import climusic.audioEngine as Audio
import os
from climusic.functions.filterFormats import filterFormats
from climusic.library import get_song_info
from climusic.functions.coverToAscii import cover_to_ascii
from climusic.functions.extractAudioWave import get_audio_wave
import json
import random
from pathlib import Path

# One place for everything
APP_DIR = Path.home() / ".climusic"
APP_DIR.mkdir(exist_ok=True)
CONFIG_PATH = APP_DIR / "config.json"
PLAYLISTS_FILE = APP_DIR / "playlists.json"
LOG_FILE = APP_DIR / "debug.log"  # Path object not a string!

def debug_log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

songs = []
songs_dir = ""

def init_library(new_dir=None):
    global songs, songs_dir
    
    if new_dir:
        songs_dir = new_dir
    
    songs = filterFormats(songs_dir)
    

def init_config():
    global songs_dir
    while True:
        if not CONFIG_PATH.exists():
            directory = input("Please enter your music directory path: ")
            if os.path.isdir(directory):
                with open(CONFIG_PATH, "w") as f:
                    json.dump({"dir": directory, "theme": "black", "visualizer": True, "shuffle": False, "repeat": False}, f)
                songs_dir = directory
                break
            else:
                print("Invalid directory")
        else:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
            songs_dir = data["dir"]
            break
    
    init_library()


    
    
def return_library():
    song_list = []
    

    for song in songs:
        if song.startswith("._") and os.name == 'nt':
            
            os.remove(os.path.join(songs_dir, song))
            continue
            
        path = os.path.join(songs_dir, song)
        info = get_song_info(path)

        if info is None:
            
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
    
    print(f"[dim]loaded {len(song_list)} songs from {songs_dir}[/dim]")
    return song_list
        
def shuffle_library(library):
    shuffled = library.copy()  
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
def set_position(position):
    Audio.set_position(position)

def load_song(index, songs):
    song = songs[index]
    cover_data = get_song_info(song["path"])["cover"]
    ascii_cover = cover_to_ascii(cover_data, width=72)
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    
    visualizer_frames = []
    if config.get("visualizer", True):
        visualizer_frames = get_audio_wave(song["path"])
    
    return {
        "song": song,
        "ascii_cover": ascii_cover,
        "visualizer_frames": visualizer_frames,  
    }



def filter_songs_alphabetically(songs, sort_by="title"):
    """
    Sort songs alphabetically
    
    Args:
        songs: list of song dicts
        sort_by: "title", "artist", or "album"
    
    Returns:
        sorted list
    """
    return sorted(songs, key=lambda s: s[sort_by].lower())

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
        return False  
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
def remove_from_playlist(playlist_name, song):
    """Remove song from playlist"""
    playlists = get_playlists()
    if playlist_name not in playlists:
        return False
    if song in playlists[playlist_name]:
        playlists[playlist_name].remove(song)
        save_playlists(playlists)
        return True
    return False
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