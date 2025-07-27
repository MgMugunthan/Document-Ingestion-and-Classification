from kafka import KafkaProducer
import json
import os

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Folder where sample files are stored
SAMPLES_DIR = 'samples'

# Simple classifier based on filename
def classify(filename):
    name = filename.lower()
    if "invoice" in name:
        return "invoice"
    elif "resume" in name:
        return "resume"
    elif "form" in name:
        return "form"
    else:
        return "default"

# Track how many messages sent
count = 0

# Loop through all files regardless of extension
for fname in os.listdir(SAMPLES_DIR):
    file_path = os.path.join(SAMPLES_DIR, fname)
    if os.path.isfile(file_path):  # Just in case there are subfolders
        doc_type = classify(fname)
        doc_id = os.path.splitext(fname)[0]  # removes extension

        msg = {
            "document_id": doc_id,
            "type": doc_type,
            "path": file_path
        }

        print(f"📤 Sending: {doc_id} as {doc_type}")
        producer.send("doc.classified", value=msg)
        count += 1

producer.flush()
print(f"[✓] Sent {count} documents")
print("✅ All documents sent to 'doc.classified'")
