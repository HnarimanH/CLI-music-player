from textual.widgets import DataTable
from climusic.functions.turnicateText import truncate

class SongTable(DataTable):
    def __init__(self, **kwargs):
        super().__init__(id="song-table", **kwargs)

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_column("#", width=5)
        self.add_column("Title", width=30)
        self.add_column("Artist", width=20)
        self.add_column("Album", width=25)
        self.add_column("Duration", width=10)

    def load_songs(self, songs_list):
        self.clear()
        for i, song in enumerate(songs_list, start=1):
            self.add_row(
                str(i),  # Displayed number starts from 1, but index is 0-based
                truncate(song["title"], 30).strip(),
                truncate(song["artist"], 20).strip(),
                truncate(song["album"], 25).strip(),
                song["length"]
            )