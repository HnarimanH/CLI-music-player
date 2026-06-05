import vlc

player = vlc.MediaPlayer()

def play_song(path):
    media = vlc.Media(path)
    player.set_media(media)
    player.play()

def pause_song():
    player.pause()

def stop_song():
    player.stop()

def get_position():
    return player.get_time() / 1000  # ms → sec

def get_length():
    return player.get_length() / 1000
def song_finished():
    return player.get_state() == vlc.State.Ended