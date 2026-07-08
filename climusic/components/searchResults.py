from textual.widgets import DataTable


class SearchResults(DataTable):
    def __init__(self, **kwargs):
        super().__init__(id="search-table", **kwargs)

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_column("#", width=3)
        self.add_column("Title", width=30)
        self.add_column("Duration", width=10)
        self.add_column("Channel", width=20)

    def load_results(self, results: list):
        self.clear()
        for i, r in enumerate(results, start=1):
            self.add_row(
                str(i),
                r["title"],
                r["duration"],
                r["channel"],
            )