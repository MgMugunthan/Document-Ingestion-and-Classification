import sys
import os
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer

# Add the parent directory to the system path to allow imports from the 'backend' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.database import db_manager
import logger
from genai_utils import classify_document

# Get a dedicated logger for the Classifier agent
log = logger.get_agent_logger("Classifier")

# Folder for saving debug metadata
DEBUG_OUTPUT_FOLDER = "output"

def classify_and_emit(consumer, producer):
    """
    Consumes messages from Kafka, classifies the document, and emits the result to a new topic.
    """
    log.info("Classifier agent started. Waiting for messages from 'doc.extracted' topic...")
    
    for message in consumer:
        metadata = message.value
        doc_id = metadata.get("document_id", "unknown_id")
        doc_name = metadata.get("document_name", "unknown_name")
        log.info(f"Received new message from Kafka: doc_id '{doc_id}'")

        try:
            db_manager.log_processing_step(doc_id, "classification", "started" , f"Starting Classification for {doc_name}")
            content = metadata.get("extracted_text", "")
            if not content.strip():
                log.warning(f"No 'extracted_text' found for doc_id '{doc_id}'. Skipping.")
                db_manager.log_processing_step(doc_id, "classification", "skipped", "No extracted text found")
                continue

            # Use the genai_utils function to get the classification result
            start_time = datetime.now()
            result = classify_document(content)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            category = result.get("document_type", "other").lower()
            confidence = float(result.get("confidence", 0.0))
            classified_by = result.get("classification_by", "Unknown")

            log.info(f"Doc '{doc_id}' classified as '{category}' by {classified_by} (Confidence: {confidence})")

            classification_data={
                "document_type": category,
                "confidence": confidence,
                "classification_by": classified_by
            }
            db_manager.update_document_status(doc_id, "classified", classification_data)
            db_manager.log_processing_step(
                doc_id,
                "classification",
                "completed", 
                f"Classified as {category} with {confidence:.2f} confidence by {classified_by}",
                int(processing_time)
            )


            # Prepare the message for the next Kafka topic
            output_message = {
                "document_id": doc_id,
                "document_name": doc_name,
                "type": category,
                "confidence": confidence,
                "classification_by": classified_by,
                "path": metadata.get("path"),
                "size": metadata.get("size"),
                "file_extension": metadata.get("file_extension"),
                "upload_timestamp": metadata.get("upload_timestamp", datetime.now().isoformat()),
                "classification_timestamp":datetime.now().isoformat()
            }

            # Send the classified data to the 'doc.classified' topic
            producer.send("doc.classified", value=output_message)
            producer.flush()
            log.info(f"Successfully emitted event for doc_id '{doc_id}' to 'doc.classified' topic.")

            db_manager.log_processing_step(doc_id, "classification", "forwarded", "Document sent to router")

            # Save debug metadata file
            debug_path = os.path.join(DEBUG_OUTPUT_FOLDER, f"{doc_id}.meta.json")
            os.makedirs(DEBUG_OUTPUT_FOLDER, exist_ok=True)
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4)

        except Exception as e:
            log.error(f"Failed to process message for doc_id '{doc_id}'.", exc_info=True)
            db_manager.log_processing_step(doc_id, "classification", "failed",f"Classification error: {str(e)}")

if __name__ == "__main__":
    log.info("Classifier service starting...")
    try:
        db_manager.initialize_database()
        log.info("Database connection established")
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
        sys.exit(1)
    try:
        # Kafka Producer setup
        producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        # Kafka Consumer setup
        consumer = KafkaConsumer(
            "doc.extracted",
            bootstrap_servers="localhost:9092",
            auto_offset_reset="earliest",
            group_id="classifier-group",
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )
        log.info("Successfully connected to Kafka.")
    except Exception as e:
        log.error("Could not connect to Kafka. Please ensure Kafka is running.", exc_info=True)
        sys.exit(1)

    # Start the main processing loop
    classify_and_emit(consumer, producer)
