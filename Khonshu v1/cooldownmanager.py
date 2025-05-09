import time
from pynput import keyboard, mouse
import pygame
from collections import deque
from khonshu import get_response
from TTS import speak
from process import Process
from functions import Functions, initialize_logs
from config import Config
import random
import sys
import os

class manager:
    def __init__(self):
        pygame.mixer.init()
        
        self.config = Config()
        self.functions = Functions(self.config)
        self.process = Process(self.functions)

        self.cooldowns = {
            "normal projectiles": {"cd": 0, "lu": 0},
            "heavy projectiles": {"cd": 6, "lu": 0},
            "double jump": {"cd": 6, "lu": 0},
            "jump": {"cd": 0, "lu": 0},
            "mobility hook": {"cd": 15, "lu": 0},
            "glide": {"cd": 0, "lu": 0},
            "ankh": {"cd": 11, "lu": 0},
        }

        self.recording_text = False
        self.current_text = []
        
        self.debounce_time = 0.5
        self.last_triggered = {}
        self.action_log = deque(maxlen=10)
        self.paused = False
        self.glide_start_time = None
        self.last_used = 0

        self.mapping = {
            keyboard.Key.shift: "glide",
            keyboard.KeyCode.from_char('x'): "double jump",
            keyboard.KeyCode.from_char('f'): "mobility hook",
            keyboard.KeyCode.from_char('e'): "ankh",
            keyboard.KeyCode.from_vk(97): "toggle_pause",
            keyboard.KeyCode.from_vk(99): "recalibrate",
            keyboard.KeyCode.from_char('q'): "ultimate",
            keyboard.Key.space: "jump",
            keyboard.KeyCode.from_char('/'): "text_recording",
        }

        self.LOG_FILE = "actions_log.txt"
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener = mouse.Listener(on_click=self.on_click)

    def start_text_recording(self):
        self.was_paused_before_recording = self.paused
        if not self.paused:
            self.paused = True
        self.recording_text = True
        self.current_text = []
        print("\nText recording started... (Type your message, Enter to send, Esc to cancel)")

    def handle_text_input(self, key):
        try:
            if key == keyboard.Key.enter:
                self.recording_text = False
                final_text = ''.join(self.current_text)
                print(f"\nSending to Khonshu: '{final_text}'")
                self.send_chat_message(final_text)
                if not self.was_paused_before_recording:
                    self.paused = False
                return True
            
            elif key == keyboard.Key.esc:
                self.recording_text = False
                print("\nText recording cancelled")
                if not self.was_paused_before_recording:
                    self.paused = False
                return True
            
            elif key == keyboard.Key.space:
                self.current_text.append(' ')
                sys.stdout.write(' ')
                sys.stdout.flush()
            
            elif key == keyboard.Key.backspace:
                if self.current_text:
                    self.current_text.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
                
            elif hasattr(key, 'char') and key.char is not None:
                self.current_text.append(key.char)
                sys.stdout.write(key.char)
                sys.stdout.flush()
            
        except Exception as e:
            print(f"Error handling text input: {e}")
        return False

    def send_chat_message(self, message):
        response = get_response(f"Moon Knight has sent this in chat: {message}")
        print(f"Khonshu's response: {response}")
        cleaned_response = self.process.process_command(response)
        speak(cleaned_response)

    def log_action(self, action):
        entry = f"Moon Knight has {action}\n"
        self.action_log.append(entry)
        
        with open(self.LOG_FILE, "w") as f:
            f.writelines(self.action_log)

        print(entry, end="")
        
        chance = 7 if "attempted to use" in action else 15
        if random.randint(1, chance) == 1:
            self.maybe_send_logs()

    def maybe_send_logs(self):
        if time.time() - self.last_used > 10:
            print("Triggering log sending from random input...")
            self.send_logs()

    def send_logs(self):
        print("Sending action logs to Khonshu...")
        with open(self.LOG_FILE, 'r') as f:
            actions_log = f.read()

        response = get_response(f"Here are Moon Knight's last 10 actions:\n{actions_log}")
        print(f"Khonshu's response: {response}")
        cleaned_response = self.process.process_command(response)
        speak(cleaned_response)

        initialize_logs()
        self.last_used = time.time()

    def check_cooldown(self, ability):
        if self.paused:
            return

        current_time = time.time()
        if ability in self.last_triggered and current_time - self.last_triggered[ability] < self.debounce_time:
            return
        self.last_triggered[ability] = current_time

        if current_time - self.cooldowns[ability]["lu"] > self.cooldowns[ability]["cd"]:
            self.cooldowns[ability]["lu"] = current_time
            self.log_action(f"used {ability}")
        else:
            self.log_action(f"attempted to use {ability}, but it's on cooldown!")

    def toggle_pause(self):
        self.paused = not self.paused
        print("\nInput paused" if self.paused else "\nInput resumed")

    def recalibrate(self):
        for ability in self.cooldowns:
            self.cooldowns[ability]["lu"] = 0
        print("\nMoon Knight has fallen in battle!")
        response = get_response("Moon Knight has fallen in battle.")
        print(f"Khonshu's response: {response}")
        speak(self.process.process_command(response))

    def on_press(self, key):
        if self.recording_text:
            if self.handle_text_input(key):
                return
            
        try:
            if hasattr(key, 'vk'):
                if key.vk == 97:
                    self.toggle_pause()
                    return
                elif key.vk == 99:
                    self.recalibrate()
                    return
        except AttributeError:
            pass
        
        ability = self.mapping.get(key)

        if ability == "text_recording" and not self.recording_text:
            self.start_text_recording()
            return

        if self.paused:
            return
        
        if ability == "ultimate":
            print("\nMoon Knight is attempting to use the ultimate!")
            response = get_response("Moon Knight is trying to use the ult.")
            print(f"Khonshu's response: {response}")
            speak(self.process.process_command(response))
        elif ability == "glide":
            if self.glide_start_time is None:
                self.glide_start_time = time.time()
        elif ability:
            self.check_cooldown(ability)

    def on_release(self, key):
        ability = self.mapping.get(key)

        if ability == "glide" and self.glide_start_time:
            duration = round(time.time() - self.glide_start_time, 2)
            self.log_action(f"glided for {duration} seconds")
            self.glide_start_time = None

    def on_click(self, x, y, button, pressed):
        if self.paused:
            return
        if pressed:
            if button == mouse.Button.left:
                self.check_cooldown("normal projectiles")
            elif button == mouse.Button.right:
                self.check_cooldown("heavy projectiles")

    def start(self):
        self.keyboard_listener.start()
        self.mouse_listener.start()
        self.keyboard_listener.join()
        self.mouse_listener.join()