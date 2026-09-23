from textual.widgets import DataTable


class SearchResults(DataTable):
    def __init__(self, **kwargs):
        super().__init__(id="search-table", **kwargs)

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_column("#", width=3)
        self.add_column("Title", width=24)
        self.add_column("Artist", width=18)
        self.add_column("Album", width=20)
        self.add_column("Time", width=8)

    def load_results(self, results: list):
        self.clear()
        for i, r in enumerate(results, start=1):
            artist = r.get("artist") or r.get("channel") or "Unknown"
            album = r.get("album") or "Unknown"
            self.add_row(
                str(i),
                r.get("title", "Unknown"),
                artist,
                album,
                r.get("duration", "--:--"),
            )