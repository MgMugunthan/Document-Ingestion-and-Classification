import os
import shutil
import json
import sys
import time
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

# Load routing configuration from routes.json
def load_routes_config():
    """Load routing configuration from routes.json file."""
    routes_path = os.path.join(os.path.dirname(__file__), "routes.json")
    try:
        with open(routes_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        log.error(f"Routes configuration file not found at {routes_path}")
        # Return default configuration
        return {
            "routes": {
                "resume": "resumes",
                "cv": "resumes",
                "receipt": "receipts", 
                "invoice": "invoices",
                "bill": "bills"
            },
            "default_folder": "others",
            "needs_action_folder": "needs_action",
            "confidence_threshold": 0.7
        }
    except json.JSONDecodeError as e:
        log.error(f"Error parsing routes configuration: {e}")
        return {
            "routes": {},
            "default_folder": "others", 
            "needs_action_folder": "needs_action",
            "confidence_threshold": 0.7
        }

# Load initial configuration
routes_config = load_routes_config()
DOCUMENT_ROUTES = routes_config.get("routes", {})
DEFAULT_FOLDER = routes_config.get("default_folder", "others")
NEEDS_ACTION_FOLDER = routes_config.get("needs_action_folder", "needs_action") 
CONFIDENCE_THRESHOLD = routes_config.get("confidence_threshold", 0.7)

def reload_routes_config():
    """Reload routes configuration from file."""
    global routes_config, DOCUMENT_ROUTES, DEFAULT_FOLDER, NEEDS_ACTION_FOLDER, CONFIDENCE_THRESHOLD
    try:
        routes_config = load_routes_config()
        DOCUMENT_ROUTES = routes_config.get("routes", {})
        DEFAULT_FOLDER = routes_config.get("default_folder", "others")
        NEEDS_ACTION_FOLDER = routes_config.get("needs_action_folder", "needs_action")
        CONFIDENCE_THRESHOLD = routes_config.get("confidence_threshold", 0.7)
        log.info("Routes configuration reloaded successfully")
        log.info(f"Active routes: {DOCUMENT_ROUTES}")
        log.info(f"Default folder: {DEFAULT_FOLDER}, Needs action folder: {NEEDS_ACTION_FOLDER}")
        return True
    except Exception as e:
        log.error(f"Failed to reload routes configuration: {e}")
        return False

def get_routing_stats():
    """Get current routing configuration and statistics."""
    return {
        "routes": DOCUMENT_ROUTES,
        "default_folder": DEFAULT_FOLDER,
        "needs_action_folder": NEEDS_ACTION_FOLDER,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "allowed_folders": set([NEEDS_ACTION_FOLDER, DEFAULT_FOLDER] + list(DOCUMENT_ROUTES.values()))
    }

def route_document(doc_data: dict):
    """
    Routes a document to a specific folder based on its classification type and confidence score.
    Uses routes.json configuration to determine target folders.
    """
    # Reload configuration for each document to pick up changes
    global routes_config, DOCUMENT_ROUTES, DEFAULT_FOLDER, NEEDS_ACTION_FOLDER, CONFIDENCE_THRESHOLD
    routes_config = load_routes_config()
    DOCUMENT_ROUTES = routes_config.get("routes", {})
    DEFAULT_FOLDER = routes_config.get("default_folder", "others")
    NEEDS_ACTION_FOLDER = routes_config.get("needs_action_folder", "needs_action")
    CONFIDENCE_THRESHOLD = routes_config.get("confidence_threshold", 0.7)
    
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
        # If confidence is below threshold, route to needs_action folder
        if confidence < CONFIDENCE_THRESHOLD:
            final_doc_type = NEEDS_ACTION_FOLDER
            log_reason = f"Low confidence ({confidence:.2f} < {CONFIDENCE_THRESHOLD}) - routed to '{NEEDS_ACTION_FOLDER}'"
            routing_reason = "low_confidence"
        else:
            # Check if document type has a defined route
            doc_type_lower = doc_type.lower()
            if doc_type_lower in DOCUMENT_ROUTES:
                final_doc_type = DOCUMENT_ROUTES[doc_type_lower]
                log_reason = f"High confidence ({confidence:.2f}) - routed to '{final_doc_type}' (mapped from '{doc_type}')"
                routing_reason = "mapped_route"
            else:
                # Route to default folder for undefined types
                final_doc_type = DEFAULT_FOLDER
                log_reason = f"High confidence ({confidence:.2f}) but '{doc_type}' not in defined routes - routed to '{DEFAULT_FOLDER}'"
                routing_reason = "default_route"

        target_folder = os.path.join(ROUTED_DOCS_FOLDER, final_doc_type)
        target_path = os.path.join(target_folder, os.path.basename(source_path))

        # --- File Operation ---
        try:
            # Only create predefined folders: needs_action, default, and mapped routes
            allowed_folders = set([NEEDS_ACTION_FOLDER, DEFAULT_FOLDER] + list(DOCUMENT_ROUTES.values()))
            
            if final_doc_type in allowed_folders:
                os.makedirs(target_folder, exist_ok=True)
                log.info(f"Created/ensured folder exists: {target_folder}")
            else:
                # This should not happen with the new logic, but safety fallback
                log.warning(f"Attempted to create unauthorized folder: {final_doc_type}. Routing to default.")
                final_doc_type = DEFAULT_FOLDER
                target_folder = os.path.join(ROUTED_DOCS_FOLDER, final_doc_type)
                target_path = os.path.join(target_folder, os.path.basename(source_path))
                os.makedirs(target_folder, exist_ok=True)
            
            # Use copy instead of move to avoid file locking issues
            import shutil
            try:
                shutil.copy2(source_path, target_path)
                log.info(f"File copied successfully to: {target_path}")
            except Exception as copy_error:
                log.warning(f"Copy failed, trying move operation: {str(copy_error)}")
                # Retry mechanism for Windows file locking issues
                max_retries = 3
                retry_delay = 1  # seconds
                
                for attempt in range(max_retries):
                    try:
                        shutil.move(source_path, target_path)
                        break  # Success, exit retry loop
                    except (OSError, PermissionError) as file_error:
                        if attempt < max_retries - 1:  # Not the last attempt
                            log.warning(f"File move attempt {attempt + 1} failed for doc_id '{doc_id}': {str(file_error)}. Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            raise file_error  # Re-raise on final attempt
            
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
            error_msg = f"Failed to process file for doc_id '{doc_id}': {str(e)}"
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
    
    # Log initial routing configuration
    reload_routes_config()
    stats = get_routing_stats()
    log.info(f"Routing configuration loaded:")
    log.info(f"  - Document routes: {stats['routes']}")
    log.info(f"  - Default folder: {stats['default_folder']}")
    log.info(f"  - Needs action folder: {stats['needs_action_folder']}")
    log.info(f"  - Confidence threshold: {stats['confidence_threshold']}")
    log.info(f"  - Allowed folders: {stats['allowed_folders']}")
    
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
