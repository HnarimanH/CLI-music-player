import math
import time


class AmbientVisualizer:
    def __init__(self, bars=90):
        self.bars = bars
        self.start_time = time.time()

    def next_frame(self):
        t = time.time() - self.start_time

        frame = []

        for i in range(self.bars):
            x = i / (self.bars - 1)

            # Three waves moving at different speeds
            wave1 = math.sin(x * math.pi * 2 + t * 0.7)
            wave2 = 0.35 * math.sin(x * math.pi * 8 - t * 1.3)
            wave3 = 0.15 * math.sin(x * math.pi * 18 + t * 2.1)

            value = wave1 + wave2 + wave3

            # Make the center naturally taller
            center_boost = 1 - abs(x - 0.5) * 1.3
            center_boost = max(center_boost, 0.3)

            value *= center_boost

            # Normalize to 0-1
            value = (value + 1.5) / 3.0

            value = max(0.0, min(1.0, value))

            frame.append(value)

        return frame