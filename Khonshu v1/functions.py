import ctypes
import time
import random
import os
import json
import pyautogui
import pygame
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button
from obswebsocket import obsws, requests
import pydirectinput

PUL = ctypes.POINTER(ctypes.c_ulong)

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]

class Functions:
    def __init__(self, config):
        self.config = config
        self.keyboard_controller = KeyboardController()
        self.mouse_controller = MouseController()
        self.muted = False
        pygame.mixer.init()

    def toggle_mute(self):
        self.muted = not self.muted
        self.config.volume.SetMute(self.muted, None)

    def play_macro(self, filename):
        filepath = os.path.join(self.config.MACRO_DIR, f"{filename}.json")
        if not os.path.exists(filepath):
            return
        with open(filepath, "r") as f:
            macro = json.load(f)
        start_time = time.monotonic()
        for action in macro:
            event_type, timestamp, *data = action
            while time.monotonic() - start_time < timestamp:
                time.sleep(0.001)
            if event_type == "key_press":
                self.keyboard_controller.press(eval(data[0]))
            elif event_type == "key_release":
                self.keyboard_controller.release(eval(data[0]))
            elif event_type == "mouse_press":
                x, y, button = data
                self.mouse_controller.press(eval(button))
            elif event_type == "mouse_release":
                x, y, button = data
                self.mouse_controller.release(eval(button))
            elif event_type == "mouse_move":
                dx, dy = data
                self.mouse_controller.move(dx, dy)

    def play_sound_effect(self, sound_name):
       for ext in [".mp3", ".wav"]:
           filepath = os.path.join(self.config.SOUND_EFFECTS_DIR, f"{sound_name}{ext}")
           if os.path.exists(filepath):
               pygame.mixer.music.load(filepath)
               pygame.mixer.music.play()
               return

    def press(self, key):
        if key.lower() == "shift":
            self.keyboard_controller.press(Key.shift)
            time.sleep(random.uniform(0.1, 0.2))
            self.keyboard_controller.release(Key.shift)
        elif key.lower() == "space":
            self.keyboard_controller.press(Key.space)
            time.sleep(random.uniform(0.1, 0.2))
            self.keyboard_controller.release(Key.space)
        else:
            self.keyboard_controller.press(key)
            time.sleep(random.uniform(0.1, 0.2))
            self.keyboard_controller.release(key)

    def hold(self, key, duration):
        pydirectinput.keyDown(key)
        time.sleep(duration)
        pydirectinput.keyUp(key)

    def save_clip(self):
        try:
            ws = obsws(self.config.OBS_HOST, self.config.OBS_PORT, self.config.OBS_PASSWORD)
            ws.connect()
            ws.call(requests.StartReplayBuffer())
            ws.call(requests.SaveReplayBuffer())
            ws.disconnect()
        except Exception:
            pass

    def typerandom(self, message):
        for char in message:
            self.keyboard_controller.press(char)
            time.sleep(random.uniform(0.02, 0.08))
            self.keyboard_controller.release(char)

    def chat(self, message, target):
        if target:
            pyautogui.press("enter")
            self.press("\t")
            time.sleep(0.2)
            self.typerandom(message)
            pyautogui.press("enter")
        else:
            pyautogui.press("enter")
            time.sleep(0.2)
            self.typerandom(message)
            pyautogui.press("enter")

    def move_mouse(self, dx, dy):
        extra = ctypes.c_ulong(0)
        mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=0, dwFlags=0x0001, time=0, dwExtraInfo=ctypes.pointer(extra))
        command = INPUT(type=0, mi=mi)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

    def move_smoothly(self, dx, dy, duration, steps=100):
        for _ in range(steps):
            self.move_mouse(dx // steps, dy // steps)
            time.sleep(duration / steps)

    def retreat(self):
        self.move_smoothly(2800, 800, 0.2) 
        self.press("f")  
        time.sleep(1.3)
        self.press("space")  
        time.sleep(0.3)  
        self.move_smoothly(0, -800, 0.12) 
        self.hold("shift", 4)

    def nod_yes(self):
        for _ in range(3):
            self.move_smoothly(0, -300, 0.1)
            time.sleep(0.1)
            self.move_smoothly(0, 300, 0.1)
            time.sleep(0.1)

    def nod_no(self):
        for _ in range(3):
            self.move_smoothly(-300, 0, 0.1)
            time.sleep(0.1)
            self.move_smoothly(300, 0, 0.1)
            time.sleep(0.1)

  


def initialize_logs():
    with open("actions_log.txt", 'w') as f:
        f.write("")
    with open("passive_hearing_log.txt", 'w') as f:
        f.write("")
