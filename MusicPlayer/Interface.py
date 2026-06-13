import musicController
from textual.app import App, ComposeResult
from textual.widgets import Header, DataTable
from textual.containers import Horizontal, Vertical
import json
from components.audioVisualizer import AudioVisualizer
from components.songTable import SongTable
from components.nowPlaying import NowPlaying
from components.songProgress import SongProgress
from components.miniTerminal import MiniTerminal
from components.musicPlayerActions import MusicPlayerActions
from themes import build_css


class MusicPlayer(MusicPlayerActions, App):
    with open("config.json", "r") as f:
        config = json.load(f)
    
    
    CSS = build_css()

    songsList = musicController.return_library()

    def compose(self) -> ComposeResult:
        yield Header()
        with open("config.json", "r") as f:
            config = json.load(f)
        if config["visualizer"] == True:
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

    def on_mount(self) -> None:
        self.progress_bar = self.query_one(SongProgress)
        with open("config.json", "r") as f:
            config = json.load(f)
        if config["visualizer"] == True:
            self.visualizer = self.query_one(AudioVisualizer)
        current_theme = config.get("theme", "purple")
        self.add_class(current_theme)
        self.set_interval(1 / 20, self.update_progress)

if __name__ == "__main__":
    app = MusicPlayer()
    app.run()