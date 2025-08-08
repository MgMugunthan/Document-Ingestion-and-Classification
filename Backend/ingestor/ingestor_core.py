"""
Ingestor Core Module

Core document processing logic including Kafka integration,
file handling, and document validation.
"""

import os
import sys
import time
import json
import uuid
from datetime import datetime
from pathlib import Path

# File monitoring
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Kafka messaging
from kafka import KafkaProducer

# Flask
from flask import jsonify
from werkzeug.utils import secure_filename

# Add parent directory for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger
from database.database import db_manager

class IngestorConfig:
    """Configuration for the document ingestor."""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.files_dir = os.path.join(self.base_dir, "uploads")
        self.supported_extensions = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.xlsx', '.csv']
        self.max_file_size = 500 * 1024 * 1024  # 500MB
        self.kafka_servers = 'localhost:9092'
        self.kafka_topic = 'doc.ingested'
        self.web_port = 5000
        
        # Gmail settings
        self.gmail_enabled = True  # Will be set by availability check
        self.gmail_scopes = ['https://www.googleapis.com/auth/gmail.modify']
        self.gmail_credentials_file = os.path.join(self.base_dir, 'credentials.json')
        self.gmail_token_file = os.path.join(self.base_dir, 'token.json')
        self.gmail_state_file = os.path.join(self.base_dir, 'gmail_state.json')
        self.gmail_check_interval = 10  # seconds
        
        # Ensure directories exist
        os.makedirs(self.files_dir, exist_ok=True)

class IngestorCore:
    """Core document ingestor functionality."""
    
    def __init__(self):
        self.config = IngestorConfig()
        self.log = logger.get_agent_logger("IngestorCore")
        self.kafka_producer = self._setup_kafka()
        self.db = db_manager
        self.file_observer = None
        self.api_uploaded_files = set()  # Track files uploaded via API to prevent double processing
        
    def _setup_kafka(self):
        """Initialize Kafka producer with error handling."""
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.config.kafka_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                max_block_ms=5000
            )
            self.log.info("Kafka producer initialized successfully")
            return producer
        except Exception as e:
            self.log.error(f"Failed to initialize Kafka producer: {e}")
            return None
    
    def is_valid_document(self, filename):
        """Check if file has supported extension."""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.config.supported_extensions
    
    def is_file_size_valid(self, file_path):
        """Check if file size is within limits."""
        try:
            size = os.path.getsize(file_path)
            return size <= self.config.max_file_size
        except:
            return False
    
    def read_file_content(self, file_path):
        """Safely read file content."""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            self.log.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def emit_to_kafka(self, filename, file_path, source, summary="", sender="System"):
        """Send document metadata to Kafka and log to database."""
        if not self.kafka_producer:
            self.log.error("Kafka producer not available")
            return None
        
        # Generate metadata
        doc_id = str(uuid.uuid4())
        metadata = {
            "document_id": doc_id,
            "document_name": filename,
            "path": os.path.abspath(file_path),
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "upload_timestamp": datetime.now().isoformat(timespec='seconds'),
            "source": source,
            "summary": summary,
            "sender": sender
        }
        
        try:
            # Log document to database
            doc_data = {
                'document_id': doc_id,
                'original_filename': filename,
                'file_path': os.path.abspath(file_path),
                'file_size': metadata["file_size"],
                'file_extension': os.path.splitext(filename)[1].lower(),
                'uploaded_by': sender
            }
            
            # Insert document record
            self.db.insert_document(doc_data)
            self.db.log_processing_step(doc_id, "ingestion", "started", f"Document uploaded via {source}")
            
            # Send to Kafka
            future = self.kafka_producer.send(self.config.kafka_topic, value=metadata)
            self.kafka_producer.flush(timeout=10)
            
            # Log successful emission
            self.db.log_processing_step(doc_id, "ingestion", "completed", "Document sent to extraction pipeline")
            
            self.log.info(f"[Kafka ] Sent to topic '{self.config.kafka_topic}': {filename}")
            return metadata
            
        except Exception as e:
            self.log.error(f"[Kafka ] Failed to send {filename}: {e}")
            if 'doc_id' in locals():
                self.db.log_processing_step(doc_id, "ingestion", "failed", str(e))
            return None
    
    def handle_api_upload(self, request):
        """Handle API file uploads."""
        if 'document' not in request.files:
            return jsonify({'error': 'No document file provided'}), 400

        doc_file = request.files['document']
        metadata_json = request.form.get('metadata', '{}')
        
        try:
            metadata = json.loads(metadata_json)
        except:
            metadata = {}
        
        # Extract user_id from form data if not in metadata
        if 'user_id' not in metadata:
            user_id_from_form = request.form.get('user_id')
            if user_id_from_form:
                metadata['user_id'] = user_id_from_form

        if not self.is_valid_document(doc_file.filename):
            return jsonify({'error': 'Invalid document type'}), 400

        filename = secure_filename(doc_file.filename)
        filepath = os.path.join(self.config.files_dir, filename)
        
        try:
            doc_file.save(filepath)
            
            if not self.is_file_size_valid(filepath):
                os.remove(filepath)
                return jsonify({'error': 'File too large'}), 400
            
            # Mark this file as API uploaded to prevent file watcher from processing it
            self.api_uploaded_files.add(filename)
            
            # Extract user_id directly from form or metadata with fallback to IP
            user_id_final = request.form.get('user_id') or metadata.get('user_id') or request.remote_addr or "API"
            
            # Emit to Kafka with correct user_id
            result_metadata = self.emit_to_kafka(
                filename,
                filepath,
                source="api_upload",
                summary=metadata.get('summary', 'API upload'),
                sender=user_id_final
            )
            
            # Debug logging
            self.log.info(f"API upload metadata: {metadata}")
            self.log.info(f"User ID used: {user_id_final}")
            
            if result_metadata:
                self.log.info(f"API upload successful: {filename}")
                return jsonify({
                    'status': 'success',
                    'document_id': result_metadata['document_id'],
                    'message': f'Document {filename} ingested successfully'
                })
            else:
                return jsonify({
                    'status': 'warning',
                    'message': 'File saved but Kafka notification failed'
                }), 202
            
        except Exception as e:
            self.log.error(f"API upload failed for {filename}: {e}")
            return jsonify({'error': str(e)}), 500
    
    def start_file_watcher(self):
        """Start file system monitoring."""
        class DocumentHandler(FileSystemEventHandler):
            def __init__(self, ingestor):
                self.ingestor = ingestor
                
            def on_created(self, event):
                if event.is_directory:
                    return
                
                file_path = event.src_path
                filename = os.path.basename(file_path)
                
                if not self.ingestor.is_valid_document(filename):
                    return
                
                # Skip files that were uploaded via API to prevent double processing
                if filename in self.ingestor.api_uploaded_files:
                    self.ingestor.log.info(f"Skipping file watcher processing for API uploaded file: {filename}")
                    self.ingestor.api_uploaded_files.discard(filename)  # Remove from tracking set
                    return
                
                # Wait for file to be fully written
                time.sleep(0.5)
                
                if not os.path.exists(file_path):
                    self.ingestor.log.debug(f"File no longer exists: {filename}")
                    return
                
                if not self.ingestor.is_file_size_valid(file_path):
                    try:
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        max_size_mb = self.ingestor.config.max_file_size / (1024 * 1024)
                        self.ingestor.log.warning(
                            f"File too large, skipping: {filename} ({file_size_mb:.1f}MB > {max_size_mb:.0f}MB)"
                        )
                    except FileNotFoundError:
                        self.ingestor.log.debug(f"File disappeared during size check: {filename}")
                    return
                
                self.ingestor.log.info(f"New document detected: {filename}")
                
                # Emit to Kafka
                self.ingestor.emit_to_kafka(
                    filename,
                    file_path,
                    source="file_watcher",
                    summary="Detected by file system monitor"
                )
        
        event_handler = DocumentHandler(self)
        observer = Observer()
        observer.schedule(event_handler, self.config.files_dir, recursive=False)
        observer.start()
        self.file_observer = observer
        
        self.log.info(f"File watcher started monitoring: {self.config.files_dir}")
        return observer
    
    def stop_services(self):
        """Stop all services gracefully."""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
        if self.kafka_producer:
            self.kafka_producer.close()
        self.log.info("Ingestor core services stopped")
