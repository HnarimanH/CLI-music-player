import numpy as np
import librosa
import miniaudio
import tempfile
import shutil
import os

def load_audio(path):
    ext = os.path.splitext(path)[1]
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmppath = tmp.name
    shutil.copy2(path, tmppath)
    try:
        decoded = miniaudio.decode_file(
            tmppath,
            output_format=miniaudio.SampleFormat.FLOAT32,
            nchannels=1
        )
        samples = np.frombuffer(decoded.samples, dtype=np.float32)
        return samples, decoded.sample_rate
    finally:
        os.unlink(tmppath)
def get_audio_wave(path, hopLength=4056, bars=60):
    y, sr = load_audio(path)  
    
    stft = librosa.stft(y, n_fft=512, hop_length=hopLength)
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
        normalized = [np.power(value / frame_max, 0.5) for value in frame[:bars // 2]]
        normalized = normalized[1:]
        mirrored = normalized[::-1][:-1] + normalized
        normalized_frames.append(mirrored)

    return normalized_frames