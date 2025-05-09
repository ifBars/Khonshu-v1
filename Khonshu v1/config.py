import pyaudio
from pynput.keyboard import KeyCode
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import os
import configparser

class Config:
    def __init__(self):
        # Read configuration from config.ini
        self.config_parser = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.ini')
        
        self.config_parser.read(config_path)
        
        # Audio settings
        self.AUDIO_FORMAT = getattr(pyaudio, self.config_parser.get('CLIENT', 'audio_format', fallback='paInt16'))
        self.AUDIO_CHANNELS = self.config_parser.getint('CLIENT', 'audio_channels', fallback=1)
        self.AUDIO_RATE = self.config_parser.getint('CLIENT', 'audio_rate', fallback=16000)
        self.AUDIO_CHUNK = self.config_parser.getint('CLIENT', 'audio_chunk', fallback=8192)
        
        # Model and keys
        self.TRIGGER_KEY = KeyCode.from_char(self.config_parser.get('CLIENT', 'trigger_key', fallback='t'))
        
        # Directories
        self.MACRO_DIR = os.path.join(os.getcwd(), self.config_parser.get('CLIENT', 'macro_dir', fallback='Macros'))
        self.SOUND_EFFECTS_DIR = os.path.join(os.getcwd(), self.config_parser.get('CLIENT', 'sound_effects_dir', fallback='Sound Effects'))
        
        # OBS settings
        self.OBS_HOST = self.config_parser.get('CLIENT', 'obs_host', fallback='localhost')
        self.OBS_PORT = self.config_parser.getint('CLIENT', 'obs_port', fallback=4455)
        self.OBS_PASSWORD = self.config_parser.get('CLIENT', 'obs_password', fallback='your_obs_password')
        
        # API key
        self.GEMINI_API_KEY = self.config_parser.get('CLIENT', 'gemini_api_key', fallback='AIzaSyAGX2FHQWFzVcYon7CrqQkCYlHi52wh_NE')
        
        # Audio device initialization
        self.devices = AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = self.interface.QueryInterface(IAudioEndpointVolume)
