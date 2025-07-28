import sys
import os
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer

# Add path to import genai_utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from genai_utils import classify_document

# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Kafka consumer setup
consumer = KafkaConsumer(
    "doc.extracted",  # Topic to listen to
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    group_id="classifier-group",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

DEBUG_OUTPUT_FOLDER = "Classifier/output"
os.makedirs(DEBUG_OUTPUT_FOLDER, exist_ok=True)


def classify_single_document(metadata):
    """
    Classify a single document and return MAS-compatible metadata.
    """
    try:
        content = metadata.get("extracted_text","")
        if not content.strip():
            raise ValueError("No extracted_text found in JSON.")

        result = classify_document(content)

        category = result.get("document_type", "unknown").lower()
        confidence = result.get("confidence", 0.0)

        print(f"✔️ {metadata.get('document_name', 'unknown')} → {category}")

        mas_result = {
            "document_id": str(uuid.uuid4()),
            "type": category,
            "confidence":confidence,
            "path": metadata.get("path") or metadata.get("file_path"),  # Use original path
            "size": metadata.get("size", 0),
            "file_extension": "application/pdf",
            "upload_timestamp": datetime.now().isoformat(timespec='seconds')
        }

        return mas_result, result

    except Exception as e:
        print(f"❌ Failed to classify {file_path}: {e}")
        return None, {"error": str(e)}


def consume_and_classify():
    print("📥 Waiting for extracted documents from 'doc.extracted' topic...")
    summary = []

    for message in consumer:
        metadata = message.value
        doc_name = metadata.get("document_name", "unknown")

        print(f"\n📄 Received: {doc_name}")

        mas_result, debug_result = classify_single_document(metadata)

        if mas_result:
            producer.send("doc.classified", value=mas_result)
            print(f"📤 Sent to Kafka topic 'doc.classified': {mas_result['document_id']}")
            summary.append(mas_result)

            # Save debug output (optional)
            base_name = os.path.splitext(doc_name)[0].replace(" ", "_")
            debug_path = os.path.join(DEBUG_OUTPUT_FOLDER, f"{base_name}.meta.json")
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(debug_result, f, indent=4)


    producer.flush()
    print(f"\n✅ Classification complete. {len(summary)} documents sent to Kafka.")

    # Save summary (optional)
    summary_path = os.path.join(DEBUG_OUTPUT_FOLDER, "classification_results.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)


if __name__ == "__main__":
    consume_and_classify()