from textual.widgets import DataTable
from climusic.functions.turnicateText import truncate

class SongTable(DataTable):
    def __init__(self, songs_list, **kwargs):
        super().__init__(id="song-table", **kwargs)
        self.songs_list = songs_list

    def on_mount(self) -> None:
        self.cursor_type = "row"
        # After creating the DataTable, add columns with widths
        self.add_column("Title", width=30)
        self.add_column("Artist", width=20)
        self.add_column("Album", width=25)
        self.add_column("Duration", width=10)

        # When adding rows, truncate the long fields
        for song in self.songs_list:
            self.add_row(
                (truncate(song["title"], 30)).strip(),
                (truncate(song["artist"], 20)).strip(),
                (truncate(song["album"], 25)).strip(),
                (song["length"])
            )
