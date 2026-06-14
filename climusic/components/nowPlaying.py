from textual.containers import Vertical
from textual.widgets import Static
from climusic.components.songProgress import SongProgress
from climusic.functions.timeConvert import convertToSeconds
from climusic.functions.coverToAscii import cover_to_ascii
from importlib import resources
class NowPlaying(Vertical):
    def __init__(self, **kwargs):
        super().__init__(id="now-playing", **kwargs)

    def compose(self):
        with resources.files("climusic.assets").joinpath("defaultAlbumCover.jpeg").open("rb") as f:
            cover_data = f.read()
        yield Static( cover_to_ascii(cover_data,width=72), id="AlbumAsciiCover")
        yield Static("Nothing is playing", id="SongDetails")
        yield SongProgress()

    def update_song(self, ascii_cover: str, song: dict):
        cover_widget = self.query_one("#AlbumAsciiCover", Static)
        details_widget = self.query_one("#SongDetails", Static)
        progress_bar = self.query_one(SongProgress)

        cover_widget.update(ascii_cover)

        details_widget.update(
                        f"""
Title: {song['title']}
Artist: {song['artist']}
Album: {song['album']}
Length: {song['length']}
            """
                    )

        progress_bar.update_progress(
            current=0,
            total=convertToSeconds(song["length"])
        )
