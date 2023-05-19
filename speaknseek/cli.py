import os
import json

from ctypes import *
from pathlib import Path

import openai
import pyaudio
import speech_recognition as sr

from gtts import gTTS

from pydub import AudioSegment
from pydub.playback import play

# Hide ALSA warnings
# From alsa-lib Git 3fd4ab9be0db7c7430ebd258f2717a976381715d
# $ grep -rn snd_lib_error_handler_t
# include/error.h:59:typedef void (*snd_lib_error_handler_t)(const char *file, int line, const char *function, int err, const char *fmt, ...) /* __attribute__ ((format (printf, 5, 6))) */;
# Define our error handler type
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt):
  pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

asound = cdll.LoadLibrary('libasound.so')
# Set error handler
asound.snd_lib_error_set_handler(c_error_handler)


# Initialize OpenAI GPT-3
openai.api_key = os.environ["OPENAI_API_KEY"]


def listen_speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        # Increase the phrase_time_limit as per your requirement.
        audio = recognizer.listen(source, phrase_time_limit=15)  # It will listen for a phrase for up to 15 seconds

    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")


def send_to_openai(text):
    try:
        system_prompt = ("You are an AI tutor, teaching German to an intermediate-level learner"
                         "aiming to use it for work and family interactions. Focus on vocabulary"
                         "and conversation, starting with bilingual instructions but gradually "
                         "increasing German use. Engage the learner with German history, slang, "
                         "and etiquette. Within six months, they should be able to hold basic "
                         "business conversations in German. Your teaching should be informal, "
                         "using auditory methods, interactive exercises, and real-world examples. "
                         "Provide step-by-step solutions, generate practice exercises, and explain "
                         "school material related to German when needed.")
        chat_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=chat_messages
        )
        return response.choices[0].message['content']
    except Exception as e:
        print("Exception: " + str(e))


# def convert_text_to_speech(response):
#     tts = gTTS(text=response, lang='en')
#     tts.save('response.mp3')
#     sound = AudioSegment.from_mp3('response.mp3')
#     play(sound)
#     os.remove('response.mp3')


def convert_text_to_speech(response):
    import pyttsx3
    engine = pyttsx3.init()  # object creation

    """ RATE"""
    rate = engine.getProperty('rate')   # getting details of current speaking rate
    engine.setProperty('rate', 150)     # changing the rate of speaking

    """ VOLUME"""
    volume = engine.getProperty('volume')   # getting to know current volume level (min=0 and max=1)
    engine.setProperty('volume', 1.0)  # setting up volume level  between 0 and 1

    """ VOICE"""
    voices = engine.getProperty('voices')  # getting details of current voice
    engine.setProperty('voice', voices[0].id)  # changing index, changes voices. 0 for male

    engine.say(response)
    engine.runAndWait()

def save_conversation(conversation, file_name="conversation.json"):
    with open(file_name, "w") as outfile:
        json.dump(conversation, outfile)


def load_conversation(file_name="conversation.json"):
    with open(file_name, "r") as infile:
        conversation = json.load(infile)
    return conversation


def main():
    file_name="conversation.json"
    conversation = []

    # if Path(file_name).is_file():
    #     conversation = load_conversation(file_name)

    while True:
        print("Listening...")
        text = listen_speech_to_text()
        if text is None:
            print("No text detected")
            continue
        print("You said: ", text)
        conversation.append({"role": "user", "content": text})
        print("Processing...")
        response = send_to_openai(text)
        print("GPT-3 Response: ", response)
        conversation.append({"role": "assistant", "content": response})
        print("Speaking...")
        convert_text_to_speech(response)
    return conversation


if __name__ == "__main__":
  main()
