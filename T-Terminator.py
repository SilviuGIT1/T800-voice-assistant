from dotenv import load_dotenv
load_dotenv()

import os
import wave
import json
import struct
import time
import simpleaudio as sa
import pyttsx3
import openai
import subprocess
import pygame
from vosk import Model, KaldiRecognizer

# ==== Try sounddevice, fallback to PyAudio ====
try:
    import sounddevice as sd
    USE_SOUNDDEVICE = True
    print("Using sounddevice for audio recording")
except ImportError:
    import pyaudio
    USE_SOUNDDEVICE = False
    print("sounddevice not found, using PyAudio fallback")

# =============== CONFIG ===============
OPENAI_API_KEY = os.getenv("Here you put your OPENAI KEY!")
if not OPENAI_API_KEY:
    raise ValueError("Please set your OpenAI API key.")
openai.api_key = OPENAI_API_KEY

VOSK_MODEL_PATH = os.path.expanduser("~/ai_chatbot/vosk-models/vosk-model-small-en-us-0.15")
SOUNDS_PATH = os.path.expanduser("~/ai_chatbot/sounds/")

custom_responses = {
    "who are you": {
        "text": "I am a Terminator.",
        "sounds": "ImT.wav"
    },
    "why do you kill": {
        "text": "Because you told me to",
        "sounds": "becauseYouToldMeTo.wav"
    },
    "what do you need": {
        "text": "I need your clothes, your boots and your motorcycle",
        "sounds": "iNeedYour.wav"
    },
    "don't kill anyone": {
        "text": "I will not kill anyone",
        "sounds": "iWillNotKillAnyone.wav"
    },
    "are you sure": {
        "text": "Of course, Im a Terminator",
        "sounds": "ofcImATerminator.wav"
    }
}

def play_wav(filename):
    filepath = os.path.join(SOUNDS_PATH, filename)
    if os.path.exists(filepath):
        wave_obj = sa.WaveObject.from_wave_file(filepath)
        play_obj = wave_obj.play()
        play_obj.wait_done()

def speak_with_waveform(text, color=(255, 0, 0)):
    out_path = "response.wav"
    try:
        if os.path.exists(out_path):
            os.remove(out_path)
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.save_to_file(text, out_path)
        engine.runAndWait()
    except Exception as e:
        print("pyttsx3 failed, trying espeak fallback:", e)
        subprocess.run(["espeak", "-w", out_path, text], check=True)

    # Wait until the WAV is ready
    start = time.time()
    while not (os.path.exists(out_path) and os.path.getsize(out_path) > 256):
        if time.time() - start > 5:
            raise RuntimeError("Timeout waiting for response.wav")
        time.sleep(0.05)

    # Load WAV
    wf = wave.open(out_path, "rb")
    num_channels = wf.getnchannels()
    sample_width = wf.getsampwidth()
    framerate = wf.getframerate()
    nframes = wf.getnframes()
    raw_data = wf.readframes(nframes)
    wf.close()

    # Convert raw audio to samples
    samples = struct.unpack("<" + str(len(raw_data)//2) + "h", raw_data)
    if num_channels == 2:
        samples = samples[::2]

    # Start playback
    play_obj = sa.play_buffer(raw_data, num_channels, sample_width, framerate)

    # Initialize pygame
    try:
        pygame.init()
        WIDTH, HEIGHT = 800, 240
        win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("AI Voice Waveform")
        show_window = True
    except Exception as e:
        print("Could not create pygame window:", e)
        show_window = False

    # Precompute waveform points for the full audio
    waveform = []
    step = max(1, len(samples) // WIDTH)
    center_y = HEIGHT // 2
    for i in range(0, len(samples), step):
        y = int((samples[i] / 32768) * (HEIGHT // 2)) + center_y
        waveform.append(y)

    # Scroll the waveform in sync with audio playback
    start_time = time.time()
    audio_duration = len(samples) / framerate
    running = True
    while play_obj.is_playing() and running:
        elapsed = time.time() - start_time
        # Determine which slice of waveform to display based on elapsed time
        max_index = int((elapsed / audio_duration) * len(waveform))
        if max_index > len(waveform):
            max_index = len(waveform)
        display_wave = waveform[:max_index]

        if show_window:
            win.fill((0, 0, 0))
            for x, y in enumerate(display_wave):
                pygame.draw.line(win, color, (x, center_y), (x, y))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

        time.sleep(0.01)

    if show_window:
        pygame.quit()
    play_obj.wait_done()

def play_wav_with_waveform(filename, color=(255, 0, 0)):
    filepath = os.path.join(SOUNDS_PATH, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    wf = wave.open(filepath, "rb")
    num_channels = wf.getnchannels()
    sample_width = wf.getsampwidth()
    framerate = wf.getframerate()
    nframes = wf.getnframes()

    # Play the full audio in background
    play_obj = sa.play_buffer(wf.readframes(nframes), num_channels, sample_width, framerate)
    wf.rewind()

    # Pygame setup
    try:
        pygame.init()
        WIDTH, HEIGHT = 800, 240
        win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("AI Voice Waveform")
        show_window = True
    except Exception as e:
        print("Could not create pygame window:", e)
        show_window = False

    chunk_size = int(framerate * 0.02)  # 20 ms chunks
    step = max(1, chunk_size // WIDTH)
    center_y = HEIGHT // 2

    running = True
    wf.rewind()
    start_time = time.time()

    while running and play_obj.is_playing():
        raw_chunk = wf.readframes(chunk_size)
        if not raw_chunk:
            break

        samples = struct.unpack("<" + str(len(raw_chunk)//2) + "h", raw_chunk)
        if num_channels == 2:
            samples = samples[::2]

        if show_window:
            win.fill((0, 0, 0))
            for i in range(0, len(samples), step):
                x = int(i / step)
                y = int((samples[i] / 32768) * (HEIGHT // 2)) + center_y
                pygame.draw.line(win, color, (x, center_y), (x, y))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

        time.sleep(chunk_size / framerate)

    if show_window:
        pygame.quit()
    play_obj.wait_done()


def record_audio(filename="input.wav", duration=5, fs=16000):
    print("Recording...")
    if USE_SOUNDDEVICE:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
        sd.wait()
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(recording.tobytes())
        wf.close()
    return filename

def speech_to_text(filename="input.wav"):
    model = Model(VOSK_MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)
    wf = wave.open(filename, "rb")
    text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text += result.get("text", "")
    result = json.loads(rec.FinalResult())
    text += result.get("text", "")
    return text.lower().strip()

def ask_gpt(question):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message["content"]

# ---- Continuous Listener with Conversation Mode ----
def continuous_listener():
    print("Always listening... Say 'T 800' to activate, 'goodbye' to stop.")
    model = Model(VOSK_MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)

    wake_phrases = ["t 800", "t800", "t eight hundred", "the eight hundred", "day eight hundred"]
    stop_phrases = ["goodbye", "good bye"]

    conversation_mode = False

    with sd.InputStream(samplerate=16000, channels=1, dtype="int16") as stream:
        while True:
            # --- Wake mode: wait for "T 800" ---
            while not conversation_mode:
                data, _ = stream.read(4000)
                if not rec.AcceptWaveform(data.tobytes()):
                    continue

                result = json.loads(rec.Result())
                text = result.get("text", "").lower().strip()
                if not text:
                    continue

                print(f"Heard: {text}")

                # --- STOP if needed ---
                if any(p in text for p in stop_phrases):
                    play_wav_with_waveform("goodbye.wav")
                    
                    return

                # --- Wake phrase detected ---
                if any(p in text for p in wake_phrases):
                    play_wav_with_waveform("blopblip.wav")
                    print("Activated — listening for your question...")
                    conversation_mode = True
                    break  # exit wake loop

            # --- Conversation mode: listen for questions until "goodbye" ---
            while conversation_mode:
                play_wav("listening.wav")

                filename = record_audio()
                question = speech_to_text(filename)
                if not question:
                    continue

                print(f"You said: {question}")

                # --- STOP command ---
                if any(p in question for p in stop_phrases):
                    play_wav_with_waveform("goodbye.wav")
                    conversation_mode = False
                    return

                # --- Custom responses ---
                if question in custom_responses:
                    custom = custom_responses[question]
                    print("AI:", custom["text"])
                    if "sounds" in custom and custom["sounds"]:
                        play_wav_with_waveform(custom["sounds"])
                    else:
                        speak_with_waveform(custom["text"], color=(255, 0, 0))

                # --- GPT fallback ---
                else:
                    answer = ask_gpt(question)
                    print("AI:", answer)
                    speak_with_waveform(answer, color=(255, 0, 0))

                play_wav("finished.wav")
                print("Listening for next question...")


def main():
    continuous_listener()

if __name__ == "__main__":
    main()
