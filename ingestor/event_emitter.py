import os
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer

# Kafka Setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Default save location
FILE_SAVE_DIR = os.path.join(os.path.dirname(__file__), "files")
os.makedirs(FILE_SAVE_DIR, exist_ok=True)

def emit_event(file_name, source, content_bytes=None, summary="No summary", sender="N/A"):
    # Save file if content is provided
    full_path = os.path.abspath(os.path.join(FILE_SAVE_DIR, file_name))

    if content_bytes:
        with open(full_path, "wb") as f:
            f.write(content_bytes)

    # Prepare metadata
    metadata = {
        "document_id": str(uuid.uuid4()),
        "document_name": file_name,
        "path": full_path,
        "file_size": os.path.getsize(full_path) if os.path.exists(full_path) else 0,
        "upload_timestamp": datetime.now().isoformat(timespec='seconds'),
        "source": source,
        "summary": summary,
        "sender": sender
    }

    # Send to Kafka
    producer.send("doc.ingested", value=metadata)
    print(f"[Kafka 🚀] Sent to topic 'doc.ingested': {file_name}")

    # Log to event_queue.json
    queue_path = os.path.join(os.path.dirname(__file__), "event_queue.json")
    try:
        with open(queue_path, "r") as f:
            queue = json.load(f)
    except:
        queue = []

    queue.append(metadata)
    with open(queue_path, "w") as f:
        json.dump(queue, f, indent=2)
