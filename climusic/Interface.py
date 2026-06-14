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
from climusic.musicController import CONFIG_PATH
try:
    import vlc
except Exception:
    print("❌ VLC not found!")
    print("Install VLC from https://www.videolan.org then try again.")
    print("Mac: brew install vlc")
    print("Linux: sudo apt install vlc")
    exit(1)

class Main(MusicPlayerActions, App):
    CSS = build_css()

    BINDINGS = [
        Binding("space", "action_toggle_pause", "Pause/Resume", priority=True),
        Binding("period", "action_next_song", "Next", priority=True),  
        Binding("comma", "action_prev_song", "Previous", priority=True),
        Binding("right_square_bracket", "action_vol_up", "Vol Up", priority=True),
        Binding("left_square_bracket", "action_vol_down", "Vol Down", priority=True),
    ]

    allSongs = musicController.return_library()
    songsList = allSongs

    def compose(self) -> ComposeResult:
        yield Header()
        with open(musicController.CONFIG_PATH, "r") as f:  
            config = json.load(f)
        if config["visualizer"]:
            left_panel = Vertical(
                SongTable(self.songsList),
                AudioVisualizer(),
                id="left_panel"
            )
        elif config["visualizer"] == False:
            left_panel = Horizontal(
                SongTable(self.songsList),
                id="left_panel"
            )
        yield Horizontal(
            left_panel,
            Vertical(
                NowPlaying(),
                MiniTerminal(id="terminal"),
                id="right_panel"
            )
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
        self.progress_bar = self.query_one(SongProgress)
        self.is_paused = False
        with open(musicController.CONFIG_PATH, "r") as f:  # Load here
            config = json.load(f)
        if config["visualizer"] == True:
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
        self.print_to_terminal("[dim]next.[/dim]")
        self.is_paused = False
        self.play_next_song()

    def action_prev_song(self) -> None:
        self.print_to_terminal("[dim]prev.[/dim]")
        self.is_paused = False
        self.play_previous_song()

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