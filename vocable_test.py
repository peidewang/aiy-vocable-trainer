import csv
import random
import os
import sys
import aiy.voice.tts
from aiy.board import Board, Led
from aiy.cloudspeech import CloudSpeechClient
import logging

files = []
enterPressed = False
index = 0
vocable_list = []
error_list = []
question_field = []
list_index = []
HEADER_LINE = ['Deutsch','English']
client = CloudSpeechClient()

VOLUME = 50
PITCH = 80
SPEED = 90

def askQuestion(question, optionList):
    global client 

    option = ','.join(optionList)
    question = question + option
    print(optionList)
    while True:

        say(question, 'en-GB')
        say("tell me your choice", 'en-GB')
        while True:
            logging.info('start listening')
            choice = client.recognize(language_code="en-GB")
            if choice is None:
                logging.info("you say nothing ...")
                continue
            logging.info('the choice is "%s"' % choice)
            if choice in optionList:
                logging.info("choice found in option list")
                return choice
            else:
                continue


def askUnitFileForExercise():
    # get complete unit list+
    files = os.listdir(".")
    units = getLectionFiles(files)

    # ask which unit
    unitNumber = askQuestion("There are units ",units)

    # if error record exists, ask if repeat from beginnin or repeat the error list
    if (unitNumber + '.err' in files):
        bRestartTheUnit = askQuestion("You have already practiced this Unit, say yes to start from beginning? Your options are ", ['yes', 'no'])
        if bRestartTheUnit=='yes':
            fileName = unitNumber + '.csv'
        else:
            fileName = unitNumber +'.err'
    else:
            fileName = unitNumber + '.csv'
    return fileName


def getLectionFiles(files):
    unitList = []
    for file in files:
        if file.find(".csv") != -1:
            unitList.append(file[:-4])
    return unitList


def readContent(lectionFile):
    global vocable_list
    global error_list
    global question_field
    global list_index

    with open(lectionFile, newline='', encoding='utf-8') as csvfile:
        csvReader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
        kopfzeile = csvReader.fieldnames
        for zeile in csvReader:
            vocable_list.append(zeile)

        list_length = len(vocable_list)
        list_index = list(range(0, list_length))
        # shuffel the vocable list order
        random.shuffle(list_index)

def saveToErrorTable(head_line, fehlerListe, lectionName):
    error_file_name = lectionName + '.err'
    if (len(fehlerListe) == 0 and os.path.exists(error_file_name)):
        os.remove(error_file_name)
        return

    with open(error_file_name, 'w', newline='') as csvfile:
        error_writer = csv.writer(csvfile, delimiter=';',
                                 quotechar='"', quoting=csv.QUOTE_MINIMAL)
        error_writer.writerow(head_line)
        for zeile in fehlerListe:
            error_writer.writerow(zeile)


def ask_vocable(vocable, board):

    logging.info('ask question')
    say(vocable['Deutsch'], 'de-DE')
    logging.info('Wait for answer of  "%s"' %vocable['Deutsch'])
    while True:
        board.led.state=Led.ON
        answer =client.recognize(language_code='en-GB')
        if answer is None:
            logging.info('You said nothing')
            continue
        board.led.state=Led.OFF
        logging.info('your answer is "%s"' % answer)
        return answer.lower() ==  vocable['English'].lower()

def say(content, language):
    global VOLUME, PITCH, SPEED
    aiy.voice.tts.say(content, lang=language, volume=VOLUME, pitch=PITCH, speed=SPEED, device='default')

def doTest(lectionFile):
    correct_answers = 0
    wrong_answers = 0
    vocableListe = []
    global error_list
    # lectionFile = 'lection9.csv' --> lectionName = 'lection9'
    unit_name = lectionFile[:-4]
    global vocable_list
    global list_index

    with Board() as board:
        try:
            error_list =[]
            readContent(lectionFile)

            for vocableIndex in list_index:

                vocable = vocable_list[vocableIndex]
            
                if ask_vocable(vocable, board) == True: # the answer is correct
                    correct_answers += 1
                    logging.info('bravo')
                else:  # the answer is wrong
                    wrong_answers += 1
                    logging.info('wrong answer')
                    board.led.state = Led.BLINK #blink the button
                    say("falsch, " + vocable['Deutsch'] + " ist ", 'de-DE')
                    say(vocable['English'], 'en-GB')
                    board.led.state = Led.OFF #stop blinking the button 
                    logging.info('the correct answer is "%s"' % vocable['English'])
                    error_list.append([vocable['Deutsch'], vocable['English']])
                quote = round(correct_answers/(wrong_answers + correct_answers), 2) * 100
                print("Du hast bis jetzt %d"% quote + "% richtig gemacht")
            say("Alle Tests sind durch, du hast bis jetzt %d"% quote + "% richtig gemacht", 'de-DE')
            if quote < 100:
                saveToErrorTable(HEADER_LINE, error_list, unit_name)
        except KeyboardInterrupt:
            print("du hast jetzt abgebrochen, Fehler werden dokumentiert")
            say("du hast jetzt abgebrochen, Fehler werden dokumentiert", 'de-DE')
            saveToErrorTable(HEADER_LINE, error_list, unit_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) == 1: 
        lectionFile = askUnitFileForExercise()
    else:
        lectionFile = sys.argv[1] + '.csv'
    doTest(lectionFile)

