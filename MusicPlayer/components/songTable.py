from textual.widgets import DataTable


class SongTable(DataTable):
    def __init__(self, songs_list, **kwargs):
        super().__init__(id="song-table", **kwargs)
        self.songs_list = songs_list

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_column("Title")
        self.add_column("Artist")

        for song in self.songs_list:
            self.add_row(
                song["title"],
                song["artist"],
            )
