import os
import json
import sys
from datetime import datetime
import pdfplumber
import pytesseract
import openpyxl
from PIL import Image
from docx import Document
from kafka import KafkaProducer, KafkaConsumer

# Add the parent directory to the system path to allow imports from the 'backend' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.database import db_manager
import logger

# Get a dedicated logger for the Extractor agent
log = logger.get_agent_logger("Extractor")

# Configure Tesseract executable path (adjust if necessary)
pytesseract.pytesseract.tesseract_cmd = r'D:\Langs\Mini Project\tesseract.exe'

# --- Text Extraction ---
def extract_text(file_path):
    """Extracts text from various file types."""
    ext = os.path.splitext(file_path)[1].lower()
    log.info(f"Attempting to extract text from '{os.path.basename(file_path)}' (type: {ext})")
    try:
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif ext in [".png", ".jpg", ".jpeg"]:
            return pytesseract.image_to_string(Image.open(file_path))
        elif ext == ".docx":
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        elif ext in [".xlsx", ".xls"]:
            wb = openpyxl.load_workbook(file_path)
            text = ""
            for sheet in wb:
                for row in sheet.iter_rows(values_only=True):
                    text += "\t".join([str(cell) if cell else "" for cell in row]) + "\n"
            return text
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            log.warning(f"Unsupported file type '{ext}' for file: {file_path}")
            return ""
    except Exception as e:
        log.error(f"Failed to extract text from {file_path}", exc_info=True)
        return ""

# --- Kafka Processing Loop ---
def process_messages(consumer, producer):
    """Consumes messages from Kafka, extracts text, and handles user interaction for blank files."""
    log.info("Extractor agent started. Waiting for messages from 'doc.ingested' topic...")
    
    processed_ids = set()
    NEEDS_ACTION_DIR = os.path.join(os.path.dirname(__file__), "..", "router", "routed_documents", "Needs_Action")
    os.makedirs(NEEDS_ACTION_DIR, exist_ok=True)

    for message in consumer:
        metadata = message.value
        doc_id = metadata.get("document_id", "unknown_id")
        doc_name = metadata.get("document_name", "unknown_name")
        
        if doc_id in processed_ids:
            log.warning(f"Skipping duplicate document: {doc_name} (ID: {doc_id})")
            continue
        
        log.info(f"Received new message from Kafka: doc_id '{doc_id}' for doc_name '{doc_name}'")
        
        try:
            # 🔥 NEW: Log extraction start
            db_manager.log_processing_step(doc_id, "extraction", "started", f"Starting text extraction for {doc_name}")
            
            path = metadata.get("path")
            if not path or not os.path.exists(path):
                error_msg = f"File not found at path '{path}' for doc_id '{doc_id}'"
                log.error(error_msg)
                # 🔥 NEW: Log error
                db_manager.log_processing_step(doc_id, "extraction", "failed", error_msg)
                continue

            # Extract text with timing
            start_time = datetime.now()
            text = extract_text(path)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            if not text.strip():
                log.warning(f"No text extracted from '{doc_name}'. Automatically routing to Needs_Action folder.")
                
                # 🔥 NEW: Log warning
                db_manager.log_processing_step(doc_id, "extraction", "warning", "No text extracted - awaiting user action", int(processing_time))
                
                # Automatically route to Needs_Action folder without user prompt
                new_path = os.path.join(NEEDS_ACTION_DIR, doc_name)
                os.rename(path, new_path)
                log.info(f"Automatically routed blank file to 'Needs_Action': {new_path}")
                
                # Update document status to needs_action for frontend to handle
                db_manager.update_document_status(doc_id, "needs_action")
                db_manager.log_processing_step(doc_id, "extraction", "needs_action", f"Routed to Needs_Action folder: {new_path}")
                
                continue # Move to the next message

            # --- Process and emit message with extracted text ---
            text_length = len(text)
            log.info(f"Successfully extracted {text_length} characters from '{doc_name}'.")
            
            # 🔥 NEW: Update document status and log success
            db_manager.update_document_status(doc_id, "extracted")
            db_manager.log_processing_step(
                doc_id, 
                "extraction", 
                "completed", 
                f"Text extraction successful - {text_length} characters extracted",
                int(processing_time)
            )
            
            output_message = metadata.copy()
            output_message["extracted_text"] = text
            output_message["text_length"] = text_length  # 🔥 NEW: Add text length
            output_message["extraction_timestamp"] = datetime.now().isoformat()  # 🔥 NEW: Add timestamp
            
            producer.send("doc.extracted", value=output_message)
            producer.flush()
            log.info(f"Successfully emitted event for doc_id '{doc_id}' to 'doc.extracted' topic.")
            
            # 🔥 NEW: Log successful forwarding
            db_manager.log_processing_step(doc_id, "extraction", "forwarded", "Document sent to classification stage")
            
            processed_ids.add(doc_id)

        except Exception as e:
            error_msg = f"Failed to process message for doc_id '{doc_id}': {str(e)}"
            log.error(error_msg, exc_info=True)
            # 🔥 NEW: Log error to database
            db_manager.log_processing_step(doc_id, "extraction", "failed", error_msg)

# --- Main Execution ---
if __name__ == "__main__":
    log.info("Extractor service starting...")

    # 🔥 NEW: Initialize database
    try:
        db_manager.initialize_database()
        log.info("Extractor service database connection ready")
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
        sys.exit(1)

    try:
        producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        consumer = KafkaConsumer(
            "doc.ingested",
            bootstrap_servers="localhost:9092",
            auto_offset_reset="earliest",
            group_id="extractor-group",
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )
        log.info("Successfully connected to Kafka.")
    except Exception as e:
        log.error("Could not connect to Kafka. Please ensure Kafka is running.", exc_info=True)
        sys.exit(1)

    process_messages(consumer, producer)