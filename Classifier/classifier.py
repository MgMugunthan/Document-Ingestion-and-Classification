import os
import json
import requests
from kafka import KafkaConsumer, KafkaProducer
from configfile import GOOGLE_API_KEY

# Kafka Setup
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Track processed documents
processed_ids = set()

def classify_with_gemini(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
    prompt = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Classify the type of document shown below using one or two words only "
                            '(e.g., "invoice", "resume", "contract", "report", etc). '
                            "Do not explain your answer. Just respond with the label.\n\n"
                            f"Document content:\n{text}"
                        )
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=prompt)
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        return candidates[0]["content"]["parts"][0]["text"].strip() if candidates else "unknown"
    except Exception as e:
        print(f"[⚠️] Gemini classification failed: {e}")
        return "unknown"

def process_document(metadata):
    """Process a document from Kafka message"""
    doc_id = metadata.get("document_id")
    if doc_id in processed_ids:
        print(f"[Classifier ⚠️] Skipping duplicate: {doc_id}")
        return
    processed_ids.add(doc_id)

    # Get the extracted text from the message
    extracted_text = metadata.get("extracted_text", "")
    if not extracted_text.strip():
        print(f"[Classifier ⚠️] No text found for: {doc_id}")
        return

    print(f"[Classifier 📥] Processing: {metadata.get('document_name', 'unknown')} ({doc_id})")

    # Classify the document
    doc_type = classify_with_gemini(extracted_text)
    
    # Add classification to metadata
    metadata["type"] = doc_type.lower()

    # Send to next stage (Router)
    producer.send("doc.classified", value=metadata)
    print(f"[Classifier 📤] Classified as '{doc_type}' → sent to router")

if __name__ == "__main__":
    # Listen to Kafka for documents from extractor
    consumer = KafkaConsumer(
        "doc.extracted",  # This is where extractor sends data
        bootstrap_servers="kafka:9092",
        group_id="classifier-group",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    print("[Classifier 🔄] Listening to Kafka topic 'doc.extracted'...")

    for message in consumer:
        metadata = message.value
        process_document(metadata)