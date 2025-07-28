import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

INCOMING_DIR = "received_docs"

class IncomingFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            print(f"[Watcher] New file detected: {file_path}")
            # 🧩 Step 2: Extractor
            print("[Pipeline] Running extractor...")
            subprocess.run(["python", "extractor.py"])

            # 🧩 Step 3: Classifier
            print("[Pipeline] Running classifier...")
            subprocess.run(["python", "classifier.py"])

            # 🧩 Step 4: Router
            print("[Pipeline] Running router...")
            subprocess.run(["python", "router.py"])

            print("[Pipeline] ✅ All steps completed.\n")

if __name__ == "__main__":
    print(f"[Watcher] Monitoring folder: {INCOMING_DIR}")
    event_handler = IncomingFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=INCOMING_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
