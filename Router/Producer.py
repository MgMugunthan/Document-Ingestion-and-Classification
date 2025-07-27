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

# Loop through files and send them to Kafka
for fname in os.listdir(SAMPLES_DIR):
    if fname.endswith(".pdf"):
        file_path = os.path.join(SAMPLES_DIR, fname)
        doc_type = classify(fname)
        doc_id = fname.replace(".pdf", "")

        msg = {
            "document_id": doc_id,
            "type": doc_type,
            "path": file_path
        }

        print(f"📤 Sending: {doc_id} as {doc_type}")
        producer.send("doc.classified", value=msg)

producer.flush()
print("✅ All documents sent to 'doc.classified'")
