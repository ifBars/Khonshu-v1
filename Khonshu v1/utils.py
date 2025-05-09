import queue
import threading
import time

task_queue = queue.Queue()

def task_worker():
    while True:
        func, args = task_queue.get()
        if func is None:
            break
        func(*args)
        task_queue.task_done()

worker_thread = threading.Thread(target=task_worker, daemon=True)
worker_thread.start()

def add_task(func, *args):
    task_queue.put((func, args))

def delay(seconds):
    time.sleep(seconds)

