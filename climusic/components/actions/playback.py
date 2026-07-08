from climusic import musicController
from climusic.audioEngine import get_position, get_length, song_finished
from climusic.components.nowPlaying import NowPlaying
import json
from climusic.musicController import CONFIG_PATH
import time


class PlayBackActions:
    # ═══════════════════════════════════════════════════════════════
    # Song Playback & Navigation
    # ═══════════════════════════════════════════════════════════════
    is_paused = False
    _last_skip_time = 0
    SKIP_TIMEOUT = 1 # seconds 
    # NEW — anchor for local time tracking
    _playback_anchor_time = 0.0
    _playback_anchor_pos = 0.0
    _last_vlc_sync = 0.0
    def load_and_play(self, index: int):
        try:
            song_data = musicController.load_song(index, songs=self.songsList)
        except FileNotFoundError as e:
            print(f"Error loading song: {e}")
            return
        self.song = song_data["song"]
        self.visualizer_frames = song_data["visualizer_frames"]
        self.ambient_visualizer = song_data["ambient_visualizer"]
        with open(CONFIG_PATH, "r") as f:
            visualizer = json.load(f).get("visualizer", True)
        if self.visualizer_frames is None and self.ambient_visualizer and visualizer:
            self.print_to_terminal(f"[red]Error: ffmpeg not installed[/red]")
            self.print_to_terminal("[red]please install ffmpeg using:[/red]")
            self.print_to_terminal("[green]python -m ffmpeg_downloader[/green]")
            self.print_to_terminal("[red]some songs need ffmpeg for their visualizer[/red]")
        musicController.play_song(self.song)
        self.query_one(NowPlaying).update_song(song_data["ascii_cover"], self.song)
        self._playback_anchor_time = time.time()
        self._playback_anchor_pos = 0
        self._last_vlc_sync = time.time()
        

    def _can_skip(self) -> bool:
        """Check if enough time has passed since last skip"""
        current_time = time.time()
        if current_time - self._last_skip_time < self.SKIP_TIMEOUT:
            return False
        self._last_skip_time = current_time
        return True

    def play_next_song(self):
        """Skip to next song in playlist"""
        if not self._can_skip():
            return
        
        if not hasattr(self, "song"):
            self.print_to_terminal("[red]no song is loaded[/red]")
            return
        
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        if config.get("repeat") == True:
            self.load_and_play(self.index)
            return
        
        self.index += 1
        if self.index >= len(self.songsList):
            self.index = 0
        
        self.load_and_play(self.index)

    def play_previous_song(self):
        """Go back to previous song in playlist"""
        if not self._can_skip():
            return
        
        if not hasattr(self, "song"):
            self.print_to_terminal("[red]no song is loaded[/red]")
            return
        
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        if config.get("repeat") == True:
            self.load_and_play(self.index)
            return
        
        self.index -= 1
        if self.index < 0:
            self.index = len(self.songsList) - 1
        
        self.load_and_play(self.index)


    def action_toggle_pause(self):
        """Toggle play/pause state"""
        if  not hasattr(self, "song"):
            self.print_to_terminal("[red]no song is loaded[/red]")
            return
        if self.is_paused:
            musicController.unpause_song()
            self.print_to_terminal("resumed.")
        else:
            musicController.pause_song()
            self.print_to_terminal("paused.")
        self.is_paused = not self.is_paused

    def forward_song(self):
        if song_finished():
            self.play_next_song()
            return
        
        current = get_position()
        total = get_length()
        
        if current < 0 or not total or total <= 0:
            return
        
        new_position = min(current + 5, total)
        musicController.set_position(new_position)

    def back_song(self):
        
        current = get_position()
        total = get_length()
        if current < 0 or not total or total <= 0:
            musicController.set_position(0)
            return
        
        new_position = max(current - 5, 0)
        musicController.set_position(new_position)


    
    # ═══════════════════════════════════════════════════════════════
    # Progress & Visualization Updates
    # ═══════════════════════════════════════════════════════════════

    def update_progress(self) -> None:
        try:
            if self.is_paused:
                return
            now = time.time()

            # only actually poll VLC ~5x/sec to resync drift, not 30x/sec
            if now - self._last_vlc_sync > 0.2:
                real_pos = get_position()
                if real_pos >= 0:
                    self._playback_anchor_pos = real_pos
                    self._playback_anchor_time = now
                self._last_vlc_sync = now

            # every tick: derive position from local clock, cheap as hell
            current = self._playback_anchor_pos + (now - self._playback_anchor_time)
            total = get_length()

            if current < 0 or not total or total <= 0:
                return
            if not hasattr(self, "visualizer_frames"):
                return
            if song_finished():
                self.play_next_song()

            if hasattr(self, "visualizer"):

                if self.ambient_visualizer is not None:
                    self.visualizer.update_wave(
                        self.ambient_visualizer.next_frame()
                    )

                elif self.visualizer_frames is not None:
                    frame_index = int((current / total) * len(self.visualizer_frames))
                    frame_index = max(
                        0,
                        min(frame_index, len(self.visualizer_frames) - 1)
                    )

                    self.visualizer.update_wave(
                        self.visualizer_frames[frame_index]
                    )

            self.progress_bar.update_progress(current, total)

        
        except Exception as e:
            self.print_to_terminal(f"[red]error: {e}[/red]")
    