import os
import json
import sys
import threading
import pdfplumber
import pytesseract
import openpyxl
from PIL import Image
from docx import Document
from kafka import KafkaProducer, KafkaConsumer

# Add the parent directory to the system path to allow imports from the 'backend' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

# Get a dedicated logger for the Extractor agent
log = logger.get_agent_logger("Extractor")

# Configure Tesseract executable path (adjust if necessary)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
        
        path = metadata.get("path")
        if not path or not os.path.exists(path):
            log.error(f"File not found at path '{path}' for doc_id '{doc_id}'. Skipping.")
            continue

        try:
            text = extract_text(path)

            if not text.strip():
                log.warning(f"No text extracted from '{doc_name}'. Waiting for user input.")
                
                # --- Interactive prompt for blank files ---
                print("\n" + "="*50)
                print(f"[ATTENTION] No text extracted from: {doc_name}")
                print("Options: [d]elete | [r]oute to 'Needs_Action' | [s]kip (default after 15s)")
                
                user_choice = {"value": None}
                def get_input():
                    user_choice["value"] = input("👉 Your choice: ").strip().lower()

                input_thread = threading.Thread(target=get_input)
                input_thread.daemon = True
                input_thread.start()
                input_thread.join(timeout=15)
                choice = user_choice["value"] or "s"
                print("="*50)

                if choice == "d":
                    os.remove(path)
                    log.info(f"User chose to delete blank file: {doc_name}")
                elif choice == "r":
                    new_path = os.path.join(NEEDS_ACTION_DIR, doc_name)
                    os.rename(path, new_path)
                    log.info(f"User chose to route blank file to 'Needs_Action': {new_path}")
                else: # 's' or timeout
                    log.info(f"Skipping blank file as per user choice/timeout: {doc_name}")
                continue # Move to the next message

            # --- Process and emit message with extracted text ---
            log.info(f"Successfully extracted text from '{doc_name}'.")
            output_message = metadata.copy()
            output_message["extracted_text"] = text
            
            producer.send("doc.extracted", value=output_message)
            producer.flush()
            log.info(f"Successfully emitted event for doc_id '{doc_id}' to 'doc.extracted' topic.")
            
            processed_ids.add(doc_id)

        except Exception as e:
            log.error(f"Failed to process message for doc_id '{doc_id}'.", exc_info=True)

# --- Main Execution ---
if __name__ == "__main__":
    log.info("Extractor service starting...")

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