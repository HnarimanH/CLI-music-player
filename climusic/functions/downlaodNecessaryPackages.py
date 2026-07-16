import sys
import subprocess
import urllib.request
import json
import yt_dlp
import ffmpeg_downloader as ffdl
import os

def check_yt_dlp_update():
    try:
        current = yt_dlp.version.__version__
        url = "https://pypi.org/pypi/yt-dlp/json"
        with urllib.request.urlopen(url, timeout=5) as r:
            latest = json.loads(r.read())["info"]["version"]
        return current, latest, current != latest
    except:
        return None, None, False

def ensure_necessary_packages():
    # ffmpeg
    if not ffdl.installed:
        print("downloading ffmpeg, one time only...")
        os.system("python -m ffmpeg_downloader install")
    ffdl.add_path()
    
    # yt-dlp — only update if outdated
    current, latest, needs_update = check_yt_dlp_update()
    if needs_update:
        print(f"updating yt-dlp {current} → {latest}...")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-U', 'yt-dlp'],
            capture_output=True
        )
        print("yt-dlp updated!")
    else:
        print(f"yt-dlp up to date ({current})")