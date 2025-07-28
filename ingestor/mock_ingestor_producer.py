import os
import json
from kafka import KafkaProducer

# Dynamically get the absolute path to the 'files' folder
FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')

# Kafka setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Ensure folder exists
if not os.path.exists(FILES_DIR):
    raise FileNotFoundError(f"Files directory not found: {FILES_DIR}")

# Send all files in the folder
for file_name in os.listdir(FILES_DIR):
    file_path = os.path.join(FILES_DIR, file_name)
    if os.path.isfile(file_path):
        metadata = {
            "document_name": file_name,
            "path": file_path.replace("\\", "/"),  # Windows safe
        }
        producer.send("doc.ingested", value=metadata)
        print(f"[Ingestor 📤] Sent: {file_name}")

producer.flush()
print("[Ingestor ✅] All files sent.")
