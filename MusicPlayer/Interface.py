import musicController
from textual.app import App, ComposeResult
from textual.widgets import Header, DataTable
from audioEngine import get_position, get_length, song_finished
from textual.containers import Horizontal, Vertical
from components.audioVisualizer import AudioVisualizer
from components.songTable import SongTable
from components.nowPlaying import NowPlaying
from components.songProgress import SongProgress
from themes import get_theme

import musicController
class MusicPlayer(App):
    ui_theme = get_theme("purple")
    accent = ui_theme["accent"]
    bg = ui_theme["background"]
    CSS = f"""
    #song-table {{
        color:{accent};
        height:50%;
        border:round {accent};
        background:{bg};
    }}

    #now-playing {{
        color:{accent};
        width: 1fr;
        height: 100%;
        background: {bg};
        border: {accent} round;
        align: center middle;
        text-align:center;
    }}

    #AlbumAsciiCover {{
        color:{accent};
        content-align: center middle;
        text-align: center;
        padding-top:1;
        padding-left:1;
    }}

    #SongDetails {{
        color:{accent};
        content-align: center middle;
        text-align: center;
    }}
    
    #SongProgress {{
        color:{accent};
        content-align: center middle;
        text-align: center;
    }}

    #SongTime {{
        color:{accent};
        content-align: center middle;
        text-align: center;
    }}

    #audio-visualizer {{
        color:{accent};
        height: 1fr;
        border: {accent} round;
        content-align: center middle;
        background:{bg};
    }}
    
    #left_panel {{
        width:60%;
    }}
    """
    
    songsList = musicController.return_library()
    def compose(self) -> ComposeResult:
        yield Header()

        

        left_panel = Vertical(
            SongTable(self.songsList),
            AudioVisualizer(),
            id="left_panel"
        )

        yield Horizontal(

            left_panel,

            NowPlaying()

        )
        return

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.index = event.cursor_row

        if self.index is None or self.index < 0:
            return

        song_data = musicController.load_song(self.index)
        
        self.song = song_data["song"]
        self.visualizer_frames = song_data["visualizer_frames"]

        musicController.play_song(self.index + 1)
        now_playing = self.query_one(NowPlaying)
        now_playing.update_song(
            song_data["ascii_cover"],
            self.song
        )

    def on_mount(self) -> None:
        self.set_interval(0.1, self.update_progress)
    
    
    def play_next_song(self):
        self.index += 1

        if self.index >= len(self.songsList):
            return
        song_data = musicController.load_song(self.index)
        
        self.song = song_data["song"]
        self.visualizer_frames = song_data["visualizer_frames"]

        musicController.play_song(self.index + 1)
        now_playing = self.query_one(NowPlaying)
        now_playing.update_song(
            song_data["ascii_cover"],
            self.song
        )
    def update_progress(self) -> None:
        
        try:
            current = get_position()
            total = get_length()
            
            
            progress_bar = self.query_one(SongProgress)
            visualizer = self.query_one(AudioVisualizer)
            
            if not hasattr(self, "visualizer_frames"):
                return

            frame_index = int(
                (current / total) * len(self.visualizer_frames)
            )

            frame_index = min(
                frame_index,
                len(self.visualizer_frames) - 1
            )

            frame = self.visualizer_frames[frame_index]

            visualizer.update_wave(frame)

            if current < 0:
                return

            progress_bar.update_progress(current,total)
            if song_finished():
                self.play_next_song()
        except Exception as e:
            print(e)

if __name__ == "__main__":
    app = MusicPlayer()
    app.run()