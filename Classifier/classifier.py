import os
import json
import uuid
from datetime import datetime
import sys

from kafka import KafkaConsumer, KafkaProducer

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logger import get_logger, log_agent_action
from genai_utils import classify_document  # ✅ Uses Gemini + Local ML fallback

logger = get_logger("classifier")

# Kafka Setup
# Using 'kafka:9092' from the dev branch for better container compatibility
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Using 'kafka:9092' from the dev branch
consumer = KafkaConsumer(
    "doc.extracted",
    bootstrap_servers="kafka:9092",
    auto_offset_reset="earliest",
    group_id="classifier-group",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

# ✅ Feature from `dev` branch to handle duplicate messages
processed_ids = set()

DEBUG_OUTPUT_FOLDER = "Classifier/output"
os.makedirs(DEBUG_OUTPUT_FOLDER, exist_ok=True)

def classify_single_document(metadata):
    try:
        content = metadata.get("extracted_text", "")
        if not content.strip():
            raise ValueError("No extracted_text found in metadata.")

        doc_name = metadata.get("document_name", "unknown")
        file_name = metadata.get("file_name", doc_name)

        # ✅ Use your Gemini + Local model classification from the Extractor branch
        result = classify_document(content)

        category = result.get("document_type", "unknown").lower()
        confidence = float(result.get("confidence", 0.0))

        logger.info(f"[✅] {doc_name} classified as '{category}' ({result.get('classification_by')}, confidence={confidence})")
        log_agent_action("classifier", metadata["document_id"], "completed", f"Classified as '{category}' using {result.get('classification_by')}")

        # ✅ Rich metadata structure from the Extractor branch
        mas_result = {
            "document_id": metadata.get("document_id", str(uuid.uuid4())),
            "document_name": doc_name,
            "file_name": file_name,
            "type": category,
            "confidence": confidence,
            "path": metadata.get("path") or metadata.get("file_path"),
            "size": metadata.get("size", 0),
            "file_extension": metadata.get("file_extension", "application/pdf"),
            "upload_timestamp": metadata.get("timestamp", datetime.now().isoformat(timespec='seconds'))
        }

        return mas_result, result

    except Exception as e:
        msg = f"❌ Failed to classify {metadata.get('document_name', 'unknown')}: {e}"
        logger.error(msg)
        log_agent_action("classifier", metadata.get("document_id", "unknown"), "error", msg)
        return None, {"error": str(e)}

def consume_and_classify():
    logger.info("Classifier agent started, waiting for documents from 'doc.extracted'")
    log_agent_action("classifier", "-", "started", "Classifier agent started and awaiting messages")
    print("📥 Waiting for extracted documents from 'doc.extracted' topic...")

    summary = []

    for message in consumer:
        metadata = message.value
        doc_id = metadata.get("document_id")
        doc_name = metadata.get("document_name", "unknown")

        # ✅ Integrate duplicate check from the dev branch
        if doc_id in processed_ids:
            logger.warning(f"Skipping duplicate document: {doc_name} ({doc_id})")
            print(f"[⚠️] Skipping duplicate: {doc_name}")
            continue
        processed_ids.add(doc_id)

        print(f"\n📄 Received: {doc_name}")
        logger.info(f"Received extracted document: {doc_name}")
        log_agent_action("classifier", doc_id, "received", f"Document received for classification: {doc_name}")

        mas_result, debug_result = classify_single_document(metadata)

        if mas_result:
            producer.send("doc.classified", value=mas_result)
            print(f"📤 Sent to Kafka topic 'doc.classified': {mas_result['document_id']}")
            logger.info(f"Sent classified metadata to 'doc.classified' for {doc_name}")
            log_agent_action("classifier", mas_result["document_id"], "emitted", "Sent classified result to topic")
            summary.append(mas_result)

            base_name = os.path.splitext(doc_name)[0].replace(" ", "_")
            debug_path = os.path.join(DEBUG_OUTPUT_FOLDER, f"{base_name}.meta.json")
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(debug_result, f, indent=4)

    producer.flush()
    print(f"\n✅ Classification complete. {len(summary)} documents sent to Kafka.")
    logger.info(f"Classification complete. {len(summary)} documents sent to Kafka.")
    log_agent_action("classifier", "-", "completed", f"Classifier finished. {len(summary)} documents classified.")

    summary_path = os.path.join(DEBUG_OUTPUT_FOLDER, "classification_results.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

if __name__ == "__main__":
    consume_and_classify()