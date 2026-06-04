
import os
import musicController
from musicController import return_library
from functions.coverToAscii import cover_to_ascii

os.system("cls" if os.name == "nt" else "clear")
library = return_library()




print(

    cover_to_ascii(library[0]["cover"],width=56)

)


while True:
    

    choice = input("enter command:")
    if choice.lower().startswith('/exit'):
        break

    if choice.lower().startswith('/p'):
        parts = choice.split()
        if len(parts) != 2:
            print("Invalid command. Use: /p <number>")
            continue
        try:
            song_number = int(parts[1])
            musicController.play_song(index = song_number)
        except ValueError:
            print('invalid song number')
        
    elif choice == "1":
        musicController.unpause_song()
    elif choice == "2":
        musicController.pause_song()
    elif choice == "3":
        musicController.stop_song()

        

