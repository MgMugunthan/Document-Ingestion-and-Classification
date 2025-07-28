import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from event_emitter import emit_event
from utils import is_valid_document
import os

# Path to the actual folder to be watched and where files stay
FILES_FOLDER = os.path.join(os.path.dirname(__file__), "files")

def read_file_bytes(file_path):
    with open(file_path, "rb") as f:
        return f.read()

class DocumentHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and is_valid_document(event.src_path):
            file_name = os.path.basename(event.src_path)
            print(f"[📁] File Created: {file_name} at {event.src_path}")

            content = read_file_bytes(event.src_path)

            emit_event(
                file_name=file_name,
                source="folder",
                content_bytes=content
            )

def start_watching():
    print(f"[INFO] Watching folder: {FILES_FOLDER}")
    if not os.path.exists(FILES_FOLDER):
        os.makedirs(FILES_FOLDER)

    observer = Observer()
    handler = DocumentHandler()
    observer.schedule(handler, FILES_FOLDER, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watching()
