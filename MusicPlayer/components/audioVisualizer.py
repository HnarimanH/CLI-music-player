from textual.widgets import Static


class AudioVisualizer(Static):
    def __init__(self):
        super().__init__(id="audio-visualizer")

    def update_wave(self, frame):
        if not frame:
            return

        visible = frame

        height = 20
        rows = []

        bar_heights = [int(v * height) for v in visible]

        for row in range(height, 0, -1):
            line = "".join(
                "██" if h >= row else "  "
                for h in bar_heights
            )
            rows.append(line)

        self.update("\n".join(rows))