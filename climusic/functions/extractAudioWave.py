import numpy as np
import librosa
import miniaudio
import tempfile
import shutil
import os

def load_audio(path):
    # miniaudio's decode_file wants an actual file path on disk, but "path" here
    # might be some weird format or location it doesn't like directly, so we make
    # a clean temp copy first, grab the file extension (.mp3, .flac, whatever)
    # so the temp file keeps the right format hint
    ext = os.path.splitext(path)[1]

    # Create a temporary file (empty for now) with that same extension.
    # delete=False means it WON'T auto-delete when closed — we gotta manually
    # clean it up later, otherwise Windows throws a fit trying to write to
    # a file that's still "open" in Python's eyes
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmppath = tmp.name  # just grab the path string, don't need the file object anymore

    # Copy the ACTUAL audio file's bytes into that temp file location
    # (copy2 preserves metadata too, not that we care about that here)
    shutil.copy2(path, tmppath)

    try:
        # Decode the temp copy into raw float32 samples, forced to mono (1 channel)
        # so we don't have to deal with stereo weirdness downstream
        decoded = miniaudio.decode_file(
            tmppath,
            output_format=miniaudio.SampleFormat.FLOAT32,
            nchannels=1
        )

        # decoded.samples is raw bytes, frombuffer reinterprets those bytes
        # as an actual numpy array of float32 numbers we can do math on
        samples = np.frombuffer(decoded.samples, dtype=np.float32)

        return samples, decoded.sample_rate  # hand back the audio data + its sample rate (hz)

    finally:
        # ALWAYS delete the temp file when we're done, success or failure.
        # Otherwise you're leaking temp
        # files onto disk every time someone loads a song. Nasty.
        os.unlink(tmppath)















def get_audio_wave(path, bars=60, rise=0.1, fall=0.05, noise_floor=0.1):
    # Load the raw audio samples + sample rate (like 44100hz, however many per second)
    y, sr = load_audio(path)

    # hopLength = "how many samples we skip between each analysis window"
    # sr // 60 means we get roughly 60 analysis frames per second of audio.
    # Smaller hopLength = more frames = smoother data, but slower to compute.
    hopLength = sr // 60

    # STFT = Short-Time Fourier Transform. Fancy way of saying:
    # "chop the audio into tiny windows, and for each window figure out
    # how much of each frequency (bass, mid, treble) is present."
    # Output is complex numbers (has magnitude + phase), we only care about magnitude (volume).
    stft = librosa.stft(y, n_fft=512, hop_length=hopLength)
    spectrogram = np.abs(stft)  # np.abs() strips out the phase junk, leaves pure "how loud is this frequency"

    # spectrogram shape is (frequency_bins, time_frames) — we transpose so it's
    # (time_frames, frequency_bins) instead, easier to loop over "one frame at a time"
    frames = spectrogram.T

    # ══════════════════════════════════════════
    # STEP 1: Frequency weighting — make bass punch harder, treble/hiss punch softer
    # ══════════════════════════════════════════
    n_freq_bins = frames.shape[1]  # how many frequency buckets exist per frame

    # Builds an array like [1.5, 1.48, 1.46, ... 0.42, 0.4]
    # First bin (lowest freq, bass) gets multiplied by 1.5 = boosted
    # Last bin (highest freq, hissy noise territory) gets multiplied by 0.4 = squashed
    # This is literally a crappy EQ curve: "care about bass, ignore hiss"
    freq_weights = np.linspace(1.5, 0.4, n_freq_bins)

    visualizer_frames = []
    for frame in frames:
        # Multiply every frequency bin by its weight — bass gets amplified, treble gets dampened
        weighted_frame = frame * freq_weights

        # We've got way more frequency bins than "bars" on screen (like 256 bins, 60 bars)
        # so we group bins into chunks and squish each chunk down to ONE number per bar
        chunk_size = max(1, len(weighted_frame) // bars)

        bar_values = []
        for i in range(bars):
            start = i * chunk_size
            end = min(len(weighted_frame), (i + 1) * chunk_size)
            if start >= len(weighted_frame):
                bar_values.append(0)
                continue
            chunk = weighted_frame[start:end]
            # np.max = "take the loudest frequency in this chunk" (not average — max looks punchier)
            bar_values.append(float(np.max(chunk)))
        visualizer_frames.append(bar_values)

    # ══════════════════════════════════════════
    # STEP 2: Normalize — scale every frame so the loudest bar = 1.0, everything else relative
    # ══════════════════════════════════════════
    normalized_frames = []
    for frame in visualizer_frames:
        frame_max = np.max(frame)  # loudest bar in THIS frame

        if frame_max <= 1e-6:
            # basically silence, dividing by ~0 = math explodes into NaN garbage
            # so just output all zeros instead of letting the universe implode
            normalized = [0.0] * (bars // 2)
        else:
            # divide every bar by the loudest one → everything's now between 0 and 1
            # np.power(x, 0.5) = square root, which makes quiet stuff look LESS quiet
            # (compresses dynamic range so visualizer doesn't look dead most of the time)
            normalized = [np.power(value / frame_max, 0.5) for value in frame[:bars // 2]]

        normalized = normalized[1:]  # drop the very first bar (usually ugly DC offset garbage)

        # Mirror it left-right so the visualizer looks symmetrical, like a classic winamp bar
        mirrored = normalized[::-1][:-1] + normalized
        normalized_frames.append(mirrored)

    # ══════════════════════════════════════════
    # STEP 3: Noise gate — kill quiet background hiss so it doesn't twitch the bars
    # ══════════════════════════════════════════
    gated_frames = []
    for frame in normalized_frames:
        gated = [
            # if a bar's value is below the noise_floor threshold, just zero it out completely
            # (that's "background hiss," not "real sound," so fuck it, ignore it)
            0.0 if v < noise_floor
            # otherwise, rescale so what's LEFT still uses the full 0–1 range
            # (without this, everything above the floor would look artificially dim)
            else (v - noise_floor) / (1 - noise_floor)
            for v in frame
        ]
        gated_frames.append(gated)

    # ══════════════════════════════════════════
    # STEP 4: Smoothing — attack fast, decay slow (so bars don't teleport/twitch)
    # ══════════════════════════════════════════
    smoothed_frames = []
    prev = [0] * len(gated_frames[0])  # starting point: everything at 0

    for frame in gated_frames:
        smoothed = []
        for new, old in zip(frame, prev):
            if new > old:
                # sound got LOUDER — snap toward it fast (rise = how big a jump per frame)
                smoothed.append(old + (new - old) * rise)
            else:
                # sound got QUIETER — ease down slowly instead of dropping instantly (fall)
                smoothed.append(old + (new - old) * fall)
        smoothed_frames.append(smoothed)
        prev = smoothed  # this frame becomes "previous" for the next loop iteration

    return smoothed_frames