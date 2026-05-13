import pygame
print(pygame.__version__)

pygame.mixer.init()

def play_song(path):
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        continue
