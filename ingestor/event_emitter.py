import os
import json
import requests
from datetime import datetime

# Paths
QUEUE_FILE = "event_queue.json"
STORED_FOLDER = "stored_docs"

# Extractor Agent IP (change this to the real IP of the extractor machine)
EXTRACTOR_URL = "http://10.195.206.230:5001/receive"  # 🔁 Replace with correct IP

# Ensure folders exist
if not os.path.exists(STORED_FOLDER):
    os.makedirs(STORED_FOLDER)

def emit_event(file_name, source, content_bytes, summary=None):
    # Save the actual document to disk
    save_path = os.path.join(STORED_FOLDER, file_name)
    with open(save_path, "wb") as f:
        f.write(content_bytes)

    # Prepare metadata event
    event = {
        "event_type": "doc.received",
        "source": source,
        "file_name": file_name,
        "timestamp": datetime.now().isoformat(),
        "summary": summary or "No summary",
        "file_path": save_path,
        "metadata": {
            "size_kb": round(len(content_bytes) / 1024, 2)
        }
    }

    # Ensure the queue file is a valid JSON list
    if not os.path.exists(QUEUE_FILE) or os.path.getsize(QUEUE_FILE) == 0:
        with open(QUEUE_FILE, 'w') as f:
            json.dump([], f)

    try:
        with open(QUEUE_FILE, 'r') as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = []
    except (json.JSONDecodeError, FileNotFoundError):
        data = []

    data.append(event)

    with open(QUEUE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"[INFO] Event written locally: {file_name} from {source}")

    # Send to extractor agent
    send_to_extractor(save_path, event)


def send_to_extractor(file_path, metadata):
    try:
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, "application/octet-stream")
            }
            data = {
                "event": json.dumps(metadata)
            }
            response = requests.post(EXTRACTOR_URL, data=data, files=files)
            print(f"[INFO] Sent to extractor: {response.json()}")
    except Exception as e:
        print(f"[ERROR] Failed to send to extractor: {str(e)}")
