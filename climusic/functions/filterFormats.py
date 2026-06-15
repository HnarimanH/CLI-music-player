import os

SUPPORTED_FORMATS = (".mp3", ".wav", ".ogg", ".flac")

MAGIC_BYTES = {
    b'\xff\xfb': 'mp3',
    b'\xff\xf3': 'mp3', 
    b'\xff\xf2': 'mp3',
    b'ID3': 'mp3',
    b'RIFF': 'wav',
    b'OggS': 'ogg',
    b'fLaC': 'flac',
}

def get_real_format(filepath):
    with open(filepath, 'rb') as f:
        header = f.read(4)
    for magic, fmt in MAGIC_BYTES.items():
        if header.startswith(magic):
            return fmt
    return None  # unknown/unsupported (m4a, aac, etc will return None)

def filterFormats(songs_dir):
    result = []
    for f in os.listdir(songs_dir):
        full = os.path.join(songs_dir, f)
        if os.path.isfile(full) and get_real_format(full) is not None:
            result.append(f)
    return result