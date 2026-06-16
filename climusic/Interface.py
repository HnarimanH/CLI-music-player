from climusic import musicController
from textual.app import App, ComposeResult, Binding
from textual.widgets import Header, DataTable
from textual.containers import Horizontal, Vertical
import json
from climusic.components.audioVisualizer import AudioVisualizer
from climusic.components.songTable import SongTable
from climusic.components.nowPlaying import NowPlaying
from climusic.components.songProgress import SongProgress
from climusic.components.miniTerminal import MiniTerminal
from climusic.components.musicPlayerActions import MusicPlayerActions
from climusic.themes import build_css
from pynput import keyboard as pynput_keyboard

try:
    import vlc
except Exception:
    print("❌ VLC not found!")
    print("Install VLC from https://www.videolan.org then try again.")
    print("Mac: brew install vlc")
    print("Linux: sudo apt install vlc")
    exit(1)

class Main(MusicPlayerActions, App):
    allSongs = []
    songsList = []

    CSS = build_css()

    BINDINGS = [
        Binding("space", "toggle_pause", "Pause/Resume", priority=True),
        Binding("d", "next_song", "Next", priority=True),
        Binding("a", "prev_song", "Previous", priority=True),
        Binding("w", "vol_up", "Vol Up", priority=True),
        Binding("s", "vol_down", "Vol Down", priority=True),
        Binding("q", "back_song", "Back", priority=True),
        Binding("e", "forward_song", "Forward", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with open(musicController.CONFIG_PATH, "r") as f:
            config = json.load(f)
        if config["visualizer"]:
            right_panel = Vertical(
                NowPlaying(),
                AudioVisualizer(),
               
                id="right_panel"
            )
        else:
            right_panel = Horizontal(
                NowPlaying(),
                id="right_panel"
            )
        
        yield Horizontal(
            Vertical(
                SongTable(),
                MiniTerminal(id="terminal"),
                id="left_panel"
            ),
            right_panel
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.index = event.cursor_row
        if self.index is None or self.index < 0:
            return
        self.load_and_play(self.index)

    def _setup_global_hotkeys(self):
        def on_press(key):
            if key == pynput_keyboard.Key.media_next:
                self.call_from_thread(self.play_next_song)
            elif key == pynput_keyboard.Key.media_previous:
                self.call_from_thread(self.play_previous_song)
            elif key == pynput_keyboard.Key.media_play_pause:
                self.call_from_thread(self.action_toggle_pause)

        listener = pynput_keyboard.Listener(on_press=on_press)
        listener.start()

    def on_mount(self) -> None:
        self.index = 0  # Initialize FIRST
        self.is_paused = False
        
        self.allSongs = musicController.return_library()
        with open(musicController.CONFIG_PATH, "r") as f:
            config = json.load(f)
        if config["shuffle"] == True:
            self.songsList = musicController.shuffle_library(self.allSongs)
        else:
            self.songsList = musicController.filter_songs_alphabetically(self.allSongs, sort_by="title")
        
        self.query_one(SongTable).load_songs(self.songsList)
        self.progress_bar = self.query_one(SongProgress)
        
        if config["visualizer"]:
            self.visualizer = self.query_one(AudioVisualizer)
        
        current_theme = config.get("theme", "purple")
        self.add_class(current_theme)
        
        self.set_interval(1 / 20, self.update_progress)
        self._setup_global_hotkeys()

    # ═══════════════════════════════════════════════════════════════
    # Key Binding Actions
    # ═══════════════════════════════════════════════════════════════

    def action_toggle_pause(self) -> None:
        if self.is_paused:
            musicController.unpause_song()
            self.print_to_terminal("[dim]resumed.[/dim]")
        else:
            musicController.pause_song()
            self.print_to_terminal("[dim]paused.[/dim]")
        self.is_paused = not self.is_paused

    def action_next_song(self) -> None:
        
        self.is_paused = False
        self.play_next_song()

    def action_prev_song(self) -> None:
        
        self.is_paused = False
        self.play_previous_song()
    
    def action_forward_song(self) -> None:
        
        self.is_paused = False
        self.forward_song()

    def action_back_song(self) -> None:
        
        self.is_paused = False
        self.back_song()

    def action_vol_up(self) -> None:
        new_vol = min(100, musicController.get_volume() + 10)
        musicController.set_volume(new_vol)
        self.print_to_terminal(f"[dim]vol: {new_vol}%[/dim]")

    def action_vol_down(self) -> None:
        new_vol = max(0, musicController.get_volume() - 10)
        musicController.set_volume(new_vol)
        self.print_to_terminal(f"[dim]vol: {new_vol}%[/dim]")


def main():
    musicController.init_config()
    app = Main()
    app.run()


if __name__ == "__main__":
    main()