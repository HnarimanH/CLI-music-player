from textual.containers import Vertical
from textual.widgets import Static


class SongProgress(Vertical):
    def __init__(self, **kwargs):
        super().__init__(id="progress-bar", **kwargs)

    def compose(self):
        yield Static("", id="SongProgress")
        yield Static("", id="SongTime")

    def update_progress(self, current, total,width = 40):
        

        if total <= 0:
            return

        filled = int((current / total) * width)

        bar = "█" * filled + "░" * (width - filled)

        self.query_one("#SongProgress").update(bar)

        current_m = int(current) // 60
        current_s = int(current) % 60

        total_m = int(total) // 60
        total_s = int(total) % 60

        self.query_one("#SongTime").update(
            f"{current_m}:{current_s:02d} / {total_m}:{total_s:02d}"
        )