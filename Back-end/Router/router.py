import os
import requests
import datetime
import shutil
import json
from kafka import KafkaConsumer
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from logger import get_logger, log_agent_action

logger = get_logger("router")

# Base folder to route documents
ROUTED_FOLDER = os.path.join(os.path.dirname(__file__), "routed_documents")

def route_document(doc_data):
    doc_id = doc_data.get("document_id")
    doc_type = doc_data.get("type", "default")
    confidence = doc_data.get("confidence", 1.0)
    source_path = os.path.abspath(doc_data.get("path"))

    if not os.path.exists(source_path):
        logger.error(f"Source file does not exist: {source_path}")
        log_agent_action("router", doc_id, "error", "Source file missing.")
        return

    # Route based on confidence
    if confidence < 0.7:
        target_folder = os.path.join(ROUTED_FOLDER, "other")
        status_msg = f"Low confidence ({confidence:.2f}), routed to 'other'"
    else:
        target_folder = os.path.join(ROUTED_FOLDER, doc_type)
        status_msg = f"High confidence ({confidence:.2f}), routed to '{doc_type}'"

    try:
        os.makedirs(target_folder, exist_ok=True)
        target_path = os.path.join(target_folder, os.path.basename(source_path))
        shutil.move(source_path, target_path)

        logger.info(f"✅ {doc_id} routed to {target_path}")
        log_agent_action("router", doc_id, "completed", status_msg)

    except Exception as e:
        logger.error(f"❌ Routing failed for {doc_id}: {str(e)}")
        log_agent_action("router", doc_id, "error", str(e))

    print(f"[✓] Routed document '{doc_id}' → {target_folder}")

if __name__ == "__main__":
    print("🚀 Starting Kafka Router...")
    logger.info("Router agent started.")
    log_agent_action("router", "-", "started", "Router agent active and listening.")

    consumer = KafkaConsumer(
        "doc.classified",
        bootstrap_servers="localhost:9092",
        group_id="router-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    print("📡 Listening on Kafka topic 'doc.classified'...")

    for message in consumer:
        doc_data = message.value
        doc_id = doc_data.get("document_id", "unknown")
        print(f"\n📄 Received document: {doc_id}")
        logger.info(f"Received doc from Kafka: {doc_id}")
        route_document(doc_data)
