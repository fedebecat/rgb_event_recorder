# In this script I want to read the file book.txt which contains several sentences.
# I then want to split the book into sentences and save them in a list.

import json
import os
import shutil
import time
import re
import enchant
import random

en_dict = enchant.Dict("en_US")

book_path = 'book.txt'
sentences = []

def check_en(sentence):
    whitelist_words = [";" , ":", "(", ")", "!", "?", ",", ".", "'", '-']
    for word in sentence:
        if en_dict.check(word) or word in whitelist_words:
            pass
        else:
            return False
    return True

# Open book and get the full text as string
with open(book_path, 'r') as book:
    book_text = book.read()

sentences = book_text.replace('\n', ' ')
sentences = sentences.split('.')

print(len(sentences))

# remove empty strings
sentences = [s for s in sentences if s]
print(len(sentences))

# split sentences with ";"
new_sentences = []
for sentence in sentences:
    if ';' in sentence:
        new_sentences += sentence.split(';')
    else:
        new_sentences.append(sentence)

print(len(new_sentences))

# remove sentences with less than 10 words and more than 20 words
new_sentences = [s for s in new_sentences if len(s.split(' ')) > 10 and len(s.split(' ')) < 20]
print(len(new_sentences))


english_sentences = [s for s in new_sentences if check_en(s)]
print(len(english_sentences))

# for _ in range(10):
#     print(random.choice(english_sentences))
#     print('')

# write all sentences in a txt file, one sentence per line
with open('sentences.txt', 'w') as outfile:
    for sentence in english_sentences:
        if len(sentence.split(' ')) < 10:
            print(sentence)
        outfile.write(sentence + '\n')

print('DONE')