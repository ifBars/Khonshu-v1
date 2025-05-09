import pyaudio
import threading
import speech_recognition as sr
import time
from pynput import keyboard
from khonshu import get_response
from TTS import speak
import random
import json
from vosk import Model, KaldiRecognizer

class AudioSystem:
    def __init__(self, config, process):
        self.config = config
        self.process = process
        self.mic = pyaudio.PyAudio()
        self.stream = self.mic.open(
            format=config.AUDIO_FORMAT,
            channels=config.AUDIO_CHANNELS,
            rate=config.AUDIO_RATE,
            input=True,
            frames_per_buffer=config.AUDIO_CHUNK
        )
        self.vosk_model = Model("vosk-model-small-en-us-0.15")
        self.recognizer = KaldiRecognizer(self.vosk_model, config.AUDIO_RATE)
        self.t_pressed = False
        self.listening = False
        self.direct_speech_in_progress = False
        self.sr_recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(device_index=1)
        self.passive_listening_active = True
        self.sr_recognizer.dynamic_energy_threshold = True
        self.sr_recognizer.energy_threshold = 4500
        self.sr_recognizer.pause_threshold = 1.2

        threading.Thread(target=self.passive_listen, daemon=True).start()

    def passive_listen(self):
        while True:
            if self.direct_speech_in_progress or not self.passive_listening_active:
                time.sleep(0.1)
                continue

            try:
                with self.microphone as source:
                    self.sr_recognizer.adjust_for_ambient_noise(source, duration=2)
                    try:
                        audio = self.sr_recognizer.listen(source, timeout=4, phrase_time_limit=7)
                        if self.direct_speech_in_progress:
                            continue

                        transcription = self.sr_recognizer.recognize_google(audio)
                        print(f"Passive Detection: {transcription}")
                        if random.random() < 0.1:
                            print(f"Moon Knight was heard saying: '{transcription}'")
                            response = get_response(f"Moon Knight was heard saying: '{transcription}'")
                            print(f"Khonshu's response: {response}")
                            cleaned_response = self.process.process_command(response)
                            speak(cleaned_response)
                    except sr.WaitTimeoutError:
                        time.sleep(0.2)
                        continue
                    except sr.UnknownValueError:
                        continue
            except Exception as e:
                print(f"Passive listening error: {e}")
                time.sleep(1)

    def process_audio(self):
        print("\nPress and hold Numpad 0 to talk.")

        def on_press(key):
            if hasattr(key, 'vk') and key.vk == 96 and not self.t_pressed:
                self.t_pressed = True
                self.direct_speech_in_progress = True
                self.listening = True
                print("Listening...")

        def on_release(key):
            if hasattr(key, 'vk') and key.vk == 96:
                self.t_pressed = False
                self.listening = False
                print("Stopped recording, processing...")

        listener_thread = threading.Thread(
            target=lambda: keyboard.Listener(on_press=on_press, on_release=on_release).start(),
            daemon=True
        )
        listener_thread.start()

        while True:
            if self.t_pressed:
                audio_data = bytearray()
                try:
                    while self.t_pressed:
                        data = self.stream.read(self.config.AUDIO_CHUNK, exception_on_overflow=False)
                        audio_data.extend(data)
                except Exception as e:
                    print(f"Audio read error: {e}")
                    self.direct_speech_in_progress = False
                    continue

                if len(audio_data) > 0:
                    print("Processing...")
                    if self.recognizer.AcceptWaveform(bytes(audio_data)):
                        result = json.loads(self.recognizer.Result())
                        transcription = result.get("text", "").strip()
                    else:
                        result = json.loads(self.recognizer.PartialResult())
                        transcription = result.get("partial", "").strip()

                    if transcription:
                        print(f"Moon Knight: {transcription}")
                        khonshu_response = get_response(transcription)
                        print(f"Khonshu: {khonshu_response}")

                        cleaned_response = self.process.process_command(khonshu_response)
                        speak(cleaned_response)
                    else:
                        print("No speech detected")

                    self.direct_speech_in_progress = False
                    print("Ready for passive listening")

            time.sleep(0.01)