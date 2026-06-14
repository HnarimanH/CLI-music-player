import keyboard
import time

def log(msg):
    with open("hotkey_debug.log", "a") as f:
        f.write(msg + "\n")

keyboard.add_hotkey("next track", lambda: log("next fired!"))
keyboard.add_hotkey("previous track", lambda: log("prev fired!"))
keyboard.add_hotkey("play/pause media", lambda: log("pause fired!"))

print("listening... press media keys")
time.sleep(10)  # 10 seconds to test