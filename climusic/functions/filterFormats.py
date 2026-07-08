import os



MAGIC_BYTES = {
    b'\xff\xfb': 'mp3',
    b'\xff\xf3': 'mp3', 
    b'\xff\xf2': 'mp3',
    b'ID3': 'mp3',
    b'RIFF': 'wav',
    b'OggS': 'ogg',
    b'fLaC': 'flac',
    b'\x1aE\xdf\xa3': 'webm',
}

def get_real_format(filepath):
    with open(filepath, 'rb') as f:
        header = f.read(12)
    
    for magic, fmt in MAGIC_BYTES.items():
        if header.startswith(magic):
            return fmt
    
    # m4a/mp4 has 'ftyp' at bytes 4-8
    if b'ftyp' in header[4:8]:
        return 'm4a'
    
    return None

SUPPORTED_FORMATS = (".mp3", ".wav", ".ogg", ".flac", ".webm", ".m4a", ".opus")

def filterFormats(songs_dir):
    result = []
    for f in os.listdir(songs_dir):
        full = os.path.join(songs_dir, f)
        if not os.path.isfile(full):
            continue
        # check magic bytes first, fall back to extension
        fmt = get_real_format(full)
        ext = os.path.splitext(f)[1].lower()
        if fmt is not None or ext in SUPPORTED_FORMATS:
            result.append(f)
    return result