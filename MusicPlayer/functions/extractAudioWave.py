import librosa
import numpy as np


def get_audio_wave(path, bars=32, hopLength = 4096):
    y, sr = librosa.load(path, sr=None, mono=True)
    y = y.astype(np.float32)
    stft = librosa.stft(
    y,
    n_fft=512,
    hop_length=hopLength
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
        
        frame_max = np.max(frame)

        normalized = [

            np.power(value / frame_max, 0.5)

            for value in frame[: bars // 2]

        ]
        normalized = normalized[1:]
        mirrored = normalized[::-1][:-1] + normalized

        normalized_frames.append(mirrored)

    return normalized_frames
