import time
import threading
from audio_system import AudioSystem
from config import Config
from process import Process
from functions import Functions
from cooldownmanager import manager
from functions import initialize_logs


def manager_thread():
    manager.start()


if __name__ == "__main__":
    config = Config()
    functions = Functions(config)
    process = Process(functions)
    audio_system = AudioSystem(config, process)

    manager = manager()
    initialize_logs()
    threading.Thread(target=manager_thread, daemon=True).start()

    audio_system.process_audio()
