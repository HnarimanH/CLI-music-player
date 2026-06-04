import librosa
import numpy as np


def get_audio_wave(path, bars=32):
    y, sr = librosa.load(path, sr=None)

    stft = librosa.stft(
    y,
    n_fft=512,
    hop_length=4096
)
    spectrogram = np.abs(stft)

    frames = spectrogram.T

    visualizer_frames = []

    for frame in frames:
        chunk_size = max(1, len(frame) // bars)
        bar_values = []

        for i in range(bars):
            start = i * chunk_size
            end = min(len(frame), (i + 1) * chunk_size)

            if start >= len(frame):
                bar_values.append(0)
                continue

            chunk = frame[start:end]
            bar_values.append(float(np.max(chunk)))

        visualizer_frames.append(bar_values)


    normalized_frames = []

    for frame in visualizer_frames:
        frame_max = max(frame) or 1

        normalized_frames.append([
            np.power(value / frame_max, 0.35)
            for value in frame
        ])

    return normalized_frames
