import os
import shutil
import json
import sys
from datetime import datetime
from kafka import KafkaConsumer

# Add the parent directory to the system path to allow imports from the 'backend' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.database import db_manager
import logger

# Get a dedicated logger for the Router agent
log = logger.get_agent_logger("Router")

# Base folder where documents will be moved after classification
ROUTED_DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "routed_documents")

def route_document(doc_data: dict):
    """
    Routes a document to a specific folder based on its classification type and confidence score.
    Enhanced with database logging.
    """
    doc_id = doc_data.get("document_id", "unknown_id")
    doc_type = doc_data.get("type", "other")  # Default to 'other' if type is missing
    confidence = doc_data.get("confidence", 0.0)
    source_path = doc_data.get("path")
    
    start_time = datetime.now()
    
    try:
        # 🔥 NEW: Log routing start
        db_manager.log_processing_step(doc_id, "routing", "started", f"Starting document routing for type: {doc_type}")

        # --- Input Validation ---
        if not source_path or not os.path.exists(source_path):
            error_msg = f"Source file not found for doc_id '{doc_id}'. Path: '{source_path}'"
            log.error(error_msg)
            # 🔥 NEW: Log error
            db_manager.log_processing_step(doc_id, "routing", "failed", error_msg)
            return

        # --- Routing Logic ---
        # If confidence is below 70%, the document is considered uncertain and moved to the 'other' folder.
        if confidence < 0.7:
            final_doc_type = "other"
            log_reason = f"Low confidence ({confidence:.2f}) - routed to 'other'"
            routing_reason = "low_confidence"
        else:
            final_doc_type = doc_type
            log_reason = f"High confidence ({confidence:.2f}) - routed to '{doc_type}'"
            routing_reason = "classified"

        target_folder = os.path.join(ROUTED_DOCS_FOLDER, final_doc_type)
        target_path = os.path.join(target_folder, os.path.basename(source_path))

        # --- File Operation ---
        try:
            os.makedirs(target_folder, exist_ok=True)
            shutil.move(source_path, target_path)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            log.info(f"Doc '{doc_id}' routed to '{final_doc_type}'. Reason: {log_reason}.")
            
            # 🔥 FIXED: Update document with final_path using new method
            db_manager.update_document_final_path(doc_id, target_path, "routed")
            
            # 🔥 NEW: Log successful routing
            db_manager.log_processing_step(
                doc_id, 
                "routing", 
                "completed", 
                f"Document routed to {final_doc_type} folder. {log_reason}. Final path: {target_path}",
                int(processing_time)
            )
            
        except Exception as e:
            error_msg = f"Failed to move file for doc_id '{doc_id}': {str(e)}"
            log.error(error_msg, exc_info=True)
            # 🔥 NEW: Log file operation error
            db_manager.log_processing_step(doc_id, "routing", "failed", error_msg)
            
    except Exception as e:
        error_msg = f"Unexpected error in routing for doc_id '{doc_id}': {str(e)}"
        log.error(error_msg, exc_info=True)
        # 🔥 NEW: Log unexpected error
        db_manager.log_processing_step(doc_id, "routing", "error", error_msg)

if __name__ == "__main__":
    log.info("Router agent starting...")
    
    # 🔥 NEW: Initialize database
    try:
        db_manager.initialize_database()
        log.info("Database connection established")
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
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
