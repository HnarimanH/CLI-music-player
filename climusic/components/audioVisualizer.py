from textual.widgets import Static

# ordered light → dark, used to fade based on how "deep" into the bar this row is
SHADES = [" ", "░", "▒", "▓", "█"]

class AudioVisualizer(Static):
    def __init__(self):
        super().__init__(id="audio-visualizer")

    def get_char(self, bar_value, row, height):
        bar_height_rows = bar_value * height

        # row itself IS the distance-from-bottom when row=height is the top line
        # (since our loop goes height → 1, and row=height prints first/top)
        depth = bar_height_rows - (row - 1)

        if depth <= 0:
            return " "
        elif depth >= 1:
            return "█"
        else:
            idx = int(depth * (len(SHADES) - 1))
            return SHADES[idx]

    def update_wave(self, frame):
        if not frame:
            return

        height = 8
        rows = []

        for row in range(height, 0, -1):
            line = "".join(self.get_char(v, row, height) for v in frame)
            rows.append(line)

        self.update("\n".join(rows))