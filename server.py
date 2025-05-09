import sys
import time
import threading
import random
import pygame
import requests
import tempfile
import os
import re
import configparser
from PyQt5.QtWidgets import QApplication, QLabel, QDesktopWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from pynput import keyboard
import socket
import pyttsx3

# Read configuration from config.ini
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
if not os.path.exists(config_path):
    config_path = 'config.ini'  # Fall back to current directory

config.read(config_path)

# Get server configuration
HOST = config.get('SERVER', 'host', fallback='127.0.0.1')
PORT = config.getint('SERVER', 'port', fallback=65432)
API_KEY = config.get('SERVER', 'api_key', fallback="cantdothatmybad")
VOICE_ID = config.get('SERVER', 'voice_id', fallback="xjBTtQPV1LP7udNEwrFu")
TTS_URL = config.get('SERVER', 'tts_url', fallback="https://api.elevenlabs.io/v1/text-to-speech/{voice_id}").format(voice_id=VOICE_ID)

pygame.mixer.init()
speech_channel = pygame.mixer.Channel(1)

class TTSConfig:
    def __init__(self):
        self.use_elevenlabs = config.getboolean('SERVER', 'use_elevenlabs', fallback=True)
        self.engine_toggle_enabled = config.getboolean('SERVER', 'engine_toggle_enabled', fallback=True)

tts_config = TTSConfig()

class Overlay(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        pixmap = QPixmap("khonshu.png")
        if pixmap.isNull():
            print("Error: Image not found or invalid format.")
            sys.exit(1)

        scaled_pixmap = pixmap.scaled(
            int(pixmap.width() * 0.75),
            int(pixmap.height() * 0.75),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.setPixmap(scaled_pixmap)
        self.resize(scaled_pixmap.size())

        self.screen = QDesktopWidget().screenGeometry(0)
        self.x_default = self.screen.width() - self.width() - 10
        self.y_up = self.screen.height() - self.height() + 120
        self.y_down = self.screen.height() - self.height() + 750

        self.shaking = False
        self.shake_timer = QTimer(self)
        self.shake_timer.setInterval(100)
        self.shake_timer.timeout.connect(self.do_shake)

        self.move_to_position(self.y_down)
        self.show()

    def animate_move(self, target_y):
        current_y = self.y()
        step = (target_y - current_y) / 25

        for i in range(25):
            if self.shaking:
                break
            current_y += step
            self.move_to_position(int(current_y))
            QApplication.processEvents()
            time.sleep(0.008)

        if target_y == self.y_down:
            self.move(self.x_default, self.y_down)

    def move_to_position(self, y):
        self.move(self.x_default, y)

    def do_shake(self):
        shake_x = random.randint(-2, 2)
        shake_y = random.randint(-1, 1)
        self.move(self.x_default + shake_x, self.y() + shake_y)

    def start_shaking(self):
        if self.shaking:
            return
        self.shaking = True
        self.shake_timer.start()

    def stop_shaking(self):
        self.shaking = False
        self.shake_timer.stop()

    def pop_up(self):
        self.animate_move(self.y_up)
        self.start_shaking()

    def pop_down(self):
        self.stop_shaking()
        self.animate_move(self.y_down)

class KeyListener(QThread):
    engine_changed = pyqtSignal(bool) 

    def run(self):
        def on_press(key):
            try:
                if key == keyboard.Key.up:
                    QTimer.singleShot(0, overlay.pop_up)
                elif key == keyboard.Key.down:
                    QTimer.singleShot(0, overlay.pop_down)
                elif hasattr(key, 'vk'):
                    if key.vk == 97:
                        tts_config.engine_toggle_enabled = not tts_config.engine_toggle_enabled
                        status = "enabled" if tts_config.engine_toggle_enabled else "disabled"
                        print(f"Engine toggling {status} (press numpad 1 again to {'enable' if not tts_config.engine_toggle_enabled else 'disable'})")
                    elif key.vk == 98:
                        if tts_config.engine_toggle_enabled:
                            tts_config.use_elevenlabs = not tts_config.use_elevenlabs
                            print(f"Switched to {'ElevenLabs' if tts_config.use_elevenlabs else 'pyttsx3'} TTS engine")
                            self.engine_changed.emit(tts_config.use_elevenlabs)
            except Exception as e:
                print("Error in key press handler:", e)

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

def parse_emotion_tags(text):
    """
    Parses text for emotion tags and returns a list of tuples with (text, emotion) pairs.
    Supports tags like [happy]text[/happy], [angry]text[/angry], etc.
    Untagged text gets 'neutral' emotion.
    """
    pattern = r'\[(.*?)\](.*?)\[/\1\]'
    segments = []
    last_pos = 0
    
    for match in re.finditer(pattern, text):
        if match.start() > last_pos:
            segments.append((text[last_pos:match.start()], "neutral"))
        
        emotion = match.group(1).lower()
        tagged_text = match.group(2)
        segments.append((tagged_text, emotion))
        last_pos = match.end()
    
    if last_pos < len(text):
        segments.append((text[last_pos:], "neutral"))
    
    return segments

def speak(text):
    def _speak():
        segments = parse_emotion_tags(text)
        
        for segment_text, emotion in segments:
            if not segment_text.strip():
                continue
                
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_filename = temp_file.name
            temp_file.close()

            if tts_config.use_elevenlabs:
                headers = {
                    "xi-api-key": API_KEY,
                    "Content-Type": "application/json"
                }
                
                emotion_settings = {
                "happy": {"stability": 0.35, "similarity_boost": 0.8, "style": 0.8, "speaker_boost": True},
                "sad": {"stability": 0.25, "similarity_boost": 0.7, "style": 0.2, "speaker_boost": False},
                "angry": {"stability": 0.7, "similarity_boost": 0.6, "style": 0.9, "speaker_boost": True},
                "excited": {"stability": 0.4, "similarity_boost": 0.85, "style": 0.85, "speaker_boost": True},
                "neutral": {"stability": 0.8, "similarity_boost": 0.85, "style": 0.37, "speaker_boost": True},
            }

                
                settings = emotion_settings.get(emotion, emotion_settings["neutral"])
                
                data = {
                    "text": segment_text,
                    "voice_settings": settings
                }
                
                try:
                    response = requests.post(TTS_URL, json=data, headers=headers)
                    if response.status_code == 200:
                        with open(temp_filename, "wb") as f:
                            f.write(response.content)
                    else:
                        print(f"Error with segment '{segment_text}':", response.text)
                        os.remove(temp_filename)
                        continue
                except Exception as e:
                    print(f"Error with segment '{segment_text}':", e)
                    os.remove(temp_filename)
                    continue
            else:
                try:
                    engine = pyttsx3.init()
                    engine.save_to_file(segment_text, temp_filename)
                    engine.runAndWait()
                    for _ in range(10):
                        if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                            break
                        time.sleep(0.1)
                    else:
                        print("Error: pyttsx3 failed to create audio file")
                        os.remove(temp_filename)
                        continue
                except Exception as e:
                    print("Error with pyttsx3:", e)
                    os.remove(temp_filename)
                    continue

            try:
                speech = pygame.mixer.Sound(temp_filename)
            except Exception as e:
                print("Error loading sound:", e)
                os.remove(temp_filename)
                continue

            QTimer.singleShot(0, overlay.pop_up)
            speech_channel.play(speech)

            while speech_channel.get_busy():
                time.sleep(0.1)

            os.remove(temp_filename)

        QTimer.singleShot(0, overlay.pop_down)

    threading.Thread(target=_speak, daemon=True).start()

class InputThread(QThread):
    def run(self):
        while True:
            user_input = input("Enter text to speak (or 'exit' to quit): ")
            if user_input.lower() == "exit":
                os._exit(0)
            speak(user_input)

class MessageReceiver(QThread):
    def run(self):
        host = '127.0.0.1'
        port = 65432

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)

        print(f"Server listening on {host}:{port}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")
            with conn:
                message = conn.recv(1024).decode()
                if message:
                    print(f"Received: {message}")
                    speak(message)
                else:
                    print("No message received.")
                conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = Overlay()

    listener_thread = KeyListener()
    listener_thread.start()

    input_thread = InputThread()
    input_thread.start()

    message_receiver_thread = MessageReceiver()
    message_receiver_thread.start()

    sys.exit(app.exec_())