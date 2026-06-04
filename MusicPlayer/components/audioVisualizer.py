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

        for row in range(height, 0, -1):
            line = ""
            for value in visible:
                bar_height = int(value * height)
                line += "██" if bar_height >= row else "  "
            rows.append(line)

        self.update("\n".join(rows))