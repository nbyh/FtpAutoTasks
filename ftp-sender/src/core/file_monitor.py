import os
import time
import watchdog.events
import watchdog.observers

class FileMonitor:
    def __init__(self, directory_to_watch, callback):
        self.directory_to_watch = directory_to_watch
        self.callback = callback
        self.observer = watchdog.observers.Observer()

    def start(self):
        event_handler = FileEventHandler(self.callback)
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.observer.stop()
        self.observer.join()

class FileEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.callback(event.src_path)