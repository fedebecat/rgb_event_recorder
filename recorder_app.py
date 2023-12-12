import os
import shutil
import time
from pynput.keyboard import Listener
from recorder_api import Recorder
import uuid
import json
import random
import requests

# the url of the webserver where the sentences are going to be displayed
url = 'http://localhost:8000'
# read sentences.txt from file and store each line in a list
sentences = []
with open('sentences.txt', 'r') as book:
    for line in book:
        sentences.append(line[:-1])


if __name__ == '__main__':
    print('starting...')
    au_indexes = ["FREE", 1, 2, 4, 6, 7, 9, 10, 12, 14, 15, 17, 23, 24, 25, 26, 27, 43, 45,
                  51, 52, 53, 54, 55, 56, "READING"]

    # ask name, surname, email to the userco
    name = input("Name: ")
    surname = input("Surname: ")
    email = input("Email: ")

    index = 0
    rep_index = 1

    rec = Recorder('recordings', au_indexes[index])
    user_hash = rec.user_id

    # serialize a json file with the user data in the recordings folder
    user_data = {"name": name, "surname": surname, "email": email, "user_hash": user_hash}
    with open(f'recordings/{user_hash}/user_data.json', 'w') as outfile:
        json.dump(user_data, outfile)

    print("READY?")
    input('Press ENTER to start...')
    print("START\n\n")

    used_sentences = dict()

    while index < len(au_indexes):
        if au_indexes[index] == "READING":
            print("\nSENTENCE:")
            print('###############################')
            print('###############################')
            s = random.choice(sentences)
            print(s)
            requests.post(url, json=s)
            print('###############################')
            print('###############################')

            with open(f'recordings/{user_hash}/AU_READING/sentences.json', 'w') as outfile:
                used_sentences[rep_index] = s
                json.dump(used_sentences, outfile)

            input('Press ENTER to start recording...')


        rec.start_recording_rgb_and_event()
        start_time = time.time()

        print("-----------------------------------------------------------------------")
        print("RECORDING AU_"+str(au_indexes[index])+" ["+str(rep_index)+" attempt]...")

        _ = input('Press ENTER to stop')

        end_time = time.time()
        total_time = end_time-start_time
        print(" TIME: " + str(total_time))
        rec.stop_recording_rgb_and_event()
        time.sleep(1)

        message = input(f'\nSelect action: \n ENTER to record next AU \n "R" to record again the current AU {au_indexes[index]} \n "E" to erase current recording and record it again. \n "Q" to quit. \n\n')

        if message == 'R':
            rep_index += 1
        elif message == 'E':
            # delete current folder from disk
            shutil.rmtree(f'{rec.log_folder}/frames_{rep_index}')
            os.remove(f'{rec.log_folder}/event_{rep_index}.raw')
        elif message == 'Q':
            break
        else:
            rep_index = 1
            index += 1
            rec.change_id(au_indexes[index])
        rec.set_directory(rep_index)

    print("-----------------------------------------------------------------------")
    print('DONE!!!')