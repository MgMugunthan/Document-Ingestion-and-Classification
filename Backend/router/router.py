import os
import os
import shutil
import json
import sys
from kafka import KafkaConsumer

# Add the parent directory to the system path to allow imports from the 'backend' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

# Get a dedicated logger for the Router agent
log = logger.get_agent_logger("Router")

# Base folder where documents will be moved after classification
ROUTED_DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "routed_documents")

def route_document(doc_data: dict):
    """
    Routes a document to a specific folder based on its classification type and confidence score.
    """
    doc_id = doc_data.get("document_id", "unknown_id")
    doc_type = doc_data.get("type", "other")  # Default to 'other' if type is missing
    confidence = doc_data.get("confidence", 0.0)
    source_path = doc_data.get("path")

    # --- Input Validation ---
    if not source_path or not os.path.exists(source_path):
        log.error(f"Source file not found for doc_id '{doc_id}'. Path: '{source_path}'")
        return

    # --- Routing Logic ---
    # If confidence is below 70%, the document is considered uncertain and moved to the 'other' folder.
    if confidence < 0.7:
        final_doc_type = "other"
        log_reason = f"Low confidence ({confidence:.2f})"
    else:
        final_doc_type = doc_type
        log_reason = f"High confidence ({confidence:.2f})"

    target_folder = os.path.join(ROUTED_DOCS_FOLDER, final_doc_type)
    target_path = os.path.join(target_folder, os.path.basename(source_path))

    # --- File Operation ---
    try:
        os.makedirs(target_folder, exist_ok=True)
        shutil.move(source_path, target_path)
        log.info(f"Doc '{doc_id}' routed to '{final_doc_type}'. Reason: {log_reason}.")
    except Exception as e:
        log.error(f"Failed to move file for doc_id '{doc_id}'.", exc_info=True)

if __name__ == "__main__":
    log.info("Router agent starting...")
    
    try:
        consumer = KafkaConsumer(
            "doc.classified",  # The Kafka topic this service listens to
            bootstrap_servers="localhost:9092",
            group_id="router-group",  # Consumer group ID
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset='earliest',  # Start reading at the earliest message
            enable_auto_commit=True
        )
        log.info("Successfully connected to Kafka. Listening on topic 'doc.classified'...")
    except Exception as e:
        log.error("Could not connect to Kafka. Please ensure Kafka is running.", exc_info=True)
        sys.exit(1) # Exit if we can't connect to Kafka

    # Continuously listen for messages from the 'doc.classified' topic
    for message in consumer:
        doc_data = message.value
        log.info(f"Received new message from Kafka: doc_id '{doc_data.get('document_id')}'")
        route_document(doc_data)
