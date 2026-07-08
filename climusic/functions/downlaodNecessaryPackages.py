import os
import subprocess
import ffmpeg_downloader as ffdl

def ensure_necessary_packages():
    if not ffdl.installed:
        print("downloading ffmpeg, one time only...")
        os.system("python -m ffmpeg_downloader")
    
    ffdl.add_path()  