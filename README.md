# T-800 Voice Assistant 

Real-time, wake-word activated AI voice assistant with offline speech-to-text, GPT fallback, voice output, and live waveform visualization. This project was later put on a Raspberry pi linux, and used only as AI assistant.

---

## Table of contents
- Quick start
- Features
- Requirements
- Install
- Run
- Start the program
- Flow

---

## Quick start
1. Clone repo  
2. Create a `.env` with your `OPENAI_API_KEY`  
3. Download a Vosk model and update `VOSK_MODEL_PATH` in the script  
4. `pip install -r requirements.txt` or install listed packages  
5. `python T-Terminator.py`  

Speak `T 800` to activate. Say `goodbye` to stop.

---

## Features
- Always-on listening mode with wake phrase `T 800`  
- Offline speech recognition using Vosk  
- GPT fallback for dynamic answers via OpenAI API  
- Text-to-speech (pyttsx3 or espeak fallback)  
- Custom sound effect playback (WAV files)  
- Real-time waveform visualization using pygame  
- Simple custom responses map for fixed replies

---

## Requirements
- Python 3.9 or newer  
- A Vosk English model (do not commit to repo)  
- An OpenAI API key  
- Recommended OS packages for audio (depends on platform: ALSA, PortAudio, or Windows audio drivers)

## Python packages:
openai
python-dotenv
vosk
pyttsx3
simpleaudio
pygame
sounddevice


---

## Install
Create a virtual environment (recommended) and install:
python -m venv venv

source venv/bin/activate   # macOS / Linux

venv\Scripts\activate      # Windows PowerShell

pip install -r requirements.txt

---

## If you do not have a requirements.txt, run:
pip install openai python-dotenv vosk pyttsx3 simpleaudio pygame sounddevice

## Update VOSK_MODEL_PATH in the script to the extracted model folder path, for example:
VOSK_MODEL_PATH = "/home/you/models/vosk-model-small-en-us-0.15"

## Start the program:
python T-Terminator.py

## Flow:
Say "T 800" to wake the assistant

Speak your question after the listening prompt

Say "goodbye" to stop the conversation and exit
