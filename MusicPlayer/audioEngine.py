import pygame
print(pygame.__version__)

pygame.mixer.init()

def play_song(path):
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
def pause_song():
    pygame.mixer.music.pause()
def unpause_song():
    pygame.mixer.music.unpause()   
def stop_song():
    pygame.mixer.music.stop()