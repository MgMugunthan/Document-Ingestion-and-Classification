from flask import Flask, request
import os
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer

# Flask app init
app = Flask(__name__)

# Correct path to store uploaded files
RECEIVE_FOLDER = os.path.join(os.path.dirname(__file__), "files")
os.makedirs(RECEIVE_FOLDER, exist_ok=True)

# Kafka Producer setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/receive', methods=['POST'])
def receive_files():
    if 'document' not in request.files or 'metadata' not in request.files:
        return "Missing files in request (need 'document' and 'metadata')", 400

    doc_file = request.files['document']
    meta_file = request.files['metadata']

    try:
        # Save the document
        doc_path = os.path.join(RECEIVE_FOLDER, doc_file.filename)
        doc_file.save(doc_path)
        print(f"[📁] Document saved: {doc_path}")

        # Read metadata JSON
        metadata = json.load(meta_file)
        metadata.update({
            "document_id": str(uuid.uuid4()),
            "document_name": doc_file.filename,
            "path": os.path.abspath(doc_path),
            "file_size": os.path.getsize(doc_path),
            "upload_timestamp": datetime.now().isoformat(timespec='seconds'),
            "source": "website"
        })

        # Send metadata to Kafka
        producer.send("doc.ingested", value=metadata)
        print(f"[Kafka 🚀] Sent to topic 'doc.ingested': {metadata['document_name']}")

        return "Document and metadata received successfully", 200

    except Exception as e:
        print(f"[❌ ERROR] {e}")
        return f"Server error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
