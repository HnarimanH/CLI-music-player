import musicController
from audioEngine import get_position, get_length, song_finished
from components.nowPlaying import NowPlaying
from components.miniTerminal import MiniTerminal


class MusicPlayerActions:
    """Mixin for song control logic. Expects self.songsList, self.visualizer, self.progress_bar."""

    def load_and_play(self, index: int):
        song_data = musicController.load_song(index, songs=self.songsList)
        self.song = song_data["song"]
        self.visualizer_frames = song_data["visualizer_frames"]
        musicController.play_song(index + 1)
        self.query_one(NowPlaying).update_song(song_data["ascii_cover"], self.song)

    def play_next_song(self):
        self.index += 1
        if self.index >= len(self.songsList):
            return
        self.load_and_play(self.index)

    def update_progress(self) -> None:
        try:
            current = get_position()
            total = get_length()

            if not total or total <= 0 or not hasattr(self, "visualizer_frames"):
                return

            frame_index = min(
                int((current / total) * len(self.visualizer_frames) - 1),
                len(self.visualizer_frames) - 1
            )
            frame_index = max(0, frame_index)  # clamp so it never goes negative

            self.visualizer.update_wave(self.visualizer_frames[frame_index])

            if current < 0:
                return

            self.progress_bar.update_progress(current, total)

            if song_finished():
                self.play_next_song()

        except Exception as e:
            self.print_to_terminal(f"[red]error: {e}[/red]")

    def handle_command(self, cmd: str):
        if cmd == "next":
            self.play_next_song()
        elif cmd == "pause":
            musicController.pause_song()
            self.print_to_terminal("paused.")
        elif cmd == "resume":
            musicController.unpause_song()
            self.print_to_terminal("resumed.")
        elif cmd == "stop":
            musicController.stop_song()
            self.print_to_terminal("stopped.")
        elif cmd.startswith("theme"):
            _, name = cmd.split(maxsplit=1)
            self.set_theme(name)
        else:
            self.print_to_terminal(f"[dim]unknown command: {cmd}[/dim]")

    def print_to_terminal(self, msg: str):
        self.query_one(MiniTerminal).write(msg)