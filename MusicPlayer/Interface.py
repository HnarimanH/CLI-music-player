import musicController
from textual.app import App, ComposeResult
from textual.widgets import Header, DataTable
from audioEngine import get_position, get_length
from textual.containers import Horizontal, Vertical
from components.audioVisualizer import AudioVisualizer
from functions.coverToAscii import cover_to_ascii
from functions.extractAudioWave import get_audio_wave
from components.songTable import SongTable
from components.nowPlaying import NowPlaying
from components.songProgress import SongProgress
class MusicPlayer(App):
    """A Textual music player interface."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    CSS = """
    #song-table {

        height:50%;
        border:round purple;
        background:black;
    }

    #now-playing {
        width: 1fr;
        height: 100%;
        background: black;
        border: round purple;
        align: center middle;
        text-align:center;
    }

    #AlbumAsciiCover {
        content-align: center middle;
        text-align: center;
        padding-top:1;
        padding-left:1;
    }

    #SongDetails {
        content-align: center middle;
        text-align: center;
    }
    
    #SongProgress {
        content-align: center middle;
        text-align: center;
    }
    #SongTime{
        content-align: center middle;
        text-align: center;
    }
    #audio-visualizer {
        height: 1fr;
        border: round purple;
        content-align: center middle;
        background:black;
    }
    """
    
    songsList = musicController.return_library()
    def compose(self) -> ComposeResult:
        yield Header()

        

        left_panel = Vertical(
            SongTable(self.songsList),
            AudioVisualizer(),
        )

        yield Horizontal(

            left_panel,

            NowPlaying()

        )
        return

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        index = event.cursor_row

        if index is None or index < 0:
            return

        self.song = self.songsList[index]
        ascii_cover = cover_to_ascii(self.song["cover"],width=72)
        self.visualizer_frames = get_audio_wave(self.song["path"])
        
        musicController.play_song(index + 1)

        now_playing = self.query_one(NowPlaying)
        now_playing.update_song(ascii_cover, self.song)

    def on_mount(self) -> None:
        self.set_interval(0.05, self.update_progress)

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
        except Exception as e:
            print(e)

if __name__ == "__main__":
    app = MusicPlayer()
    app.run()