from textual.widgets import Static


class AudioVisualizer(Static):
    def __init__(self):
        super().__init__(id="audio-visualizer")
    def get_char(self,h, row):
        ratio = row / h if h > 0 else 0
        if ratio > 0.8:
            return "░"
        elif ratio > 0.6:
            return "▒"
        elif ratio > 0.4:
            return "▓"
        else:
            return "█"
    def update_wave(self, frame):
        if not frame:
            return

        visible = frame

        height = 8
        rows = []

        bar_heights = [int(v * height) for v in visible]

        for row in range(height, 0, -1):
            line = "".join(
                self.get_char(h, row) if h >= row else " "  
                for h in bar_heights
            )
            rows.append(line)
        self.update("\n".join(rows))