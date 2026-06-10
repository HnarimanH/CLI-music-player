import musicController
from textual.app import App, ComposeResult
from textual.widgets import Header, DataTable
from textual.containers import Horizontal, Vertical

from components.audioVisualizer import AudioVisualizer
from components.songTable import SongTable
from components.nowPlaying import NowPlaying
from components.songProgress import SongProgress
from components.miniTerminal import MiniTerminal
from components.musicPlayerActions import MusicPlayerActions
from themes import get_theme, build_css


class MusicPlayer(MusicPlayerActions, App):
    ui_theme = get_theme("purple")
    CSS = build_css(ui_theme["accent"], ui_theme["background"])

    songsList = musicController.return_library()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                SongTable(self.songsList),
                AudioVisualizer(),
                id="left_panel"
            ),
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
        self.visualizer = self.query_one(AudioVisualizer)
        self.set_interval(1 / 20, self.update_progress)


if __name__ == "__main__":
    app = MusicPlayer()
    app.run()