import vlc

instance = vlc.Instance("--quiet")
player = instance.media_player_new()  # use instance, not vlc.MediaPlayer()

def play_song(path):
    media = instance.media_new(path)  # use instance here too
    player.set_media(media)
    player.play()

def pause_song():
    player.pause()

def unpause_song():
    player.set_pause(0)

def stop_song():
    player.stop()

def get_position():
    ms = player.get_time()
    return ms / 1000 if ms >= 0 else 0.0

def get_length():
    ms = player.get_length()
    return ms / 1000 if ms > 0 else 0.0

def song_finished():
    return player.get_state() == vlc.State.Ended
def set_volume(level):
    level = max(0, min(100, level))  # clamp to 0-100
    player.audio_set_volume(level)

def get_volume():
    return player.audio_get_volume()