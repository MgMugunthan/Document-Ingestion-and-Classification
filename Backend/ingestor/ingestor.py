import os
import sys
import time
import json
import uuid
import base64
import threading
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..")))
from database.database import db_manager

# Flask for web interface
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# File monitoring
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Kafka messaging
from kafka import KafkaProducer

# Gmail integration
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Gmail integration not available. Install google-api-python-client to enable.")

# Add parent directory for logger import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

# Configuration
class IngestorConfig:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.files_dir = os.path.join(self.base_dir, "uploads")
        self.supported_extensions = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.xlsx', '.csv']
        self.max_file_size = 500 * 1024 * 1024  # 500MB (increased from 100MB)
        self.kafka_servers = 'localhost:9092'
        self.kafka_topic = 'doc.ingested'
        self.web_port = 5000
        
        # Gmail settings
        self.gmail_enabled = GMAIL_AVAILABLE
        self.gmail_scopes = ['https://www.googleapis.com/auth/gmail.modify']
        self.gmail_credentials_file = os.path.join(self.base_dir, 'credentials.json')
        self.gmail_token_file = os.path.join(self.base_dir, 'token.json')
        self.gmail_state_file = os.path.join(self.base_dir, 'gmail_state.json')
        self.gmail_check_interval = 10  # seconds
        
        # Ensure directories exist
        os.makedirs(self.files_dir, exist_ok=True)
        # Note: Logs are managed centrally by logger.py

config = IngestorConfig()
log = logger.get_agent_logger("Ingestor")

class DocumentIngestor:
    def __init__(self):
        self.config = config
        self.kafka_producer = self._setup_kafka()
        self.flask_app = self._setup_flask()
        self.file_observer = None
        self.db = db_manager
        
    def _setup_kafka(self):
        """Initialize Kafka producer with error handling."""
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.config.kafka_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                max_block_ms=5000  # Don't block forever
            )
            log.info("Kafka producer initialized successfully")
            return producer
        except Exception as e:
            log.error(f"Failed to initialize Kafka producer: {e}")
            return None
    
    def _setup_flask(self):
        """Initialize Flask app with all routes."""
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            return """
            <html><head><title>Document Ingestor API</title></head>
            <body>
                <h1>Document Ingestor Service</h1>
                <p><strong>Status:</strong> Running</p>
                <p><strong>Frontend:</strong> <a href="http://localhost:3000">http://localhost:3000</a></p>
                <hr>
                <h2>API Endpoints:</h2>
                <ul>
                    <li><strong>POST /api/receive</strong> - API file upload (used by frontend)</li>
                    <li><strong>GET /api/status</strong> - Service status</li>
                    <li><strong>GET /api/document/&lt;doc_id&gt;/status</strong> - Document processing status</li>
                    <li><strong>GET /api/documents/user/&lt;user_id&gt;</strong> - User documents</li>
                    <li><strong>POST /api/gmail/fetch</strong> - Fetch Gmail attachments</li>
                    <li><strong>GET /api/gmail/status</strong> - Gmail integration status</li>
                </ul>
                <hr>
                <p><em>Use the frontend at <a href="http://localhost:3000">http://localhost:3000</a> for document upload and management.</em></p>
            </body></html>
            """
        
        @app.route('/api/receive', methods=['POST'])
        def api_receive():
            return self._handle_api_upload(request)
        
        @app.route('/api/status')
        def status():
            return jsonify({
                'status': 'running',
                'service': 'document-ingestor',
                'kafka_connected': self.kafka_producer is not None,
                'database_connected': self.db is not None,
                'watching_folder': self.config.files_dir,
                'supported_types': self.config.supported_extensions,
                'gmail_enabled': self.config.gmail_enabled,
                'endpoints': {
                    'api_receive': 'POST /api/receive',
                    'document_status': 'GET /api/document/<doc_id>/status',
                    'user_documents': 'GET /api/documents/user/<user_id>',
                    'gmail_fetch_new': 'POST /api/gmail/fetch',
                    'gmail_fetch_all': 'POST /api/gmail/fetch-all',
                    'gmail_status': 'GET /api/gmail/status',
                    'gmail_reset': 'POST /api/gmail/reset',
                    'status': 'GET /api/status'
                }
            })
        
        @app.route('/api/gmail/fetch', methods=['POST'])
        def gmail_fetch():
            """Manually trigger Gmail attachment fetching."""
            if not self.config.gmail_enabled:
                return jsonify({'error': 'Gmail integration not enabled'}), 400
            
            try:
                # Check if user wants to fetch all emails or just new ones
                fetch_all = request.json.get('fetch_all', False) if request.is_json else False
                
                self._fetch_gmail_attachments(fetch_all=fetch_all)
                mode = "all emails" if fetch_all else "new emails only"
                return jsonify({
                    'status': 'success', 
                    'message': f'Gmail fetch completed ({mode})'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/gmail/fetch-all', methods=['POST'])
        def gmail_fetch_all():
            """Manually fetch ALL unread emails with attachments (including old ones)."""
            if not self.config.gmail_enabled:
                return jsonify({'error': 'Gmail integration not enabled'}), 400
            
            try:
                self._fetch_gmail_attachments(fetch_all=True)
                return jsonify({
                    'status': 'success', 
                    'message': 'All unread Gmail attachments fetched'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/gmail/status')
        def gmail_status():
            """Get Gmail integration status and state."""
            if not self.config.gmail_enabled:
                return jsonify({'gmail_enabled': False, 'reason': 'Gmail integration not available'})
            
            last_processed = self._load_gmail_state()
            return jsonify({
                'gmail_enabled': True,
                'last_processed_timestamp': last_processed,
                'state_file_exists': os.path.exists(self.config.gmail_state_file),
                'credentials_file_exists': os.path.exists(self.config.gmail_credentials_file),
                'token_file_exists': os.path.exists(self.config.gmail_token_file)
            })
        
        @app.route('/api/gmail/reset', methods=['POST'])
        def gmail_reset():
            """Reset Gmail state to current time (ignore old emails)."""
            if not self.config.gmail_enabled:
                return jsonify({'error': 'Gmail integration not enabled'}), 400
            
            try:
                self._initialize_gmail_state()
                return jsonify({
                    'status': 'success',
                    'message': 'Gmail state reset - will only process new emails from now on'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/document/<doc_id>/status', methods=['GET'])
        def get_document_status(doc_id):
            """Get document processing status"""
            try:
                # Get document from database
                document = self.db.get_document_status(doc_id)
                
                if not document:
                    return jsonify({'error': 'Document not found'}), 404
                    
                # Convert to dict (in case it's a database row object)
                doc_dict = dict(document) if hasattr(document, 'keys') else document
                
                # Get processing logs
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT stage, status, message, timestamp 
                        FROM processing_logs 
                        WHERE document_id = %s 
                        ORDER BY timestamp ASC
                    """, (doc_id,))
                    logs = cursor.fetchall()
                    
                return jsonify({
                    'document': doc_dict,
                    'processing_logs': [
                        {
                            'stage': log[0],
                            'status': log[1], 
                            'message': log[2],
                            'timestamp': log[3].isoformat() if log[3] else None
                        } for log in logs
                    ]
                }), 200
                
            except Exception as e:
                log.error(f"Error getting document status: {e}")
                return jsonify({'error': 'Internal server error'}), 500

        @app.route('/api/documents/user/<user_id>', methods=['GET'])
        def get_user_documents(user_id):
            """Get all documents for a specific user"""
            try:
                documents = self.db.get_user_documents(user_id)
                
                # Convert to list of dicts
                docs_list = [dict(doc) for doc in documents] if documents else []
                
                return jsonify({
                    'user_id': user_id,
                    'document_count': len(docs_list),
                    'documents': docs_list
                }), 200
                
            except Exception as e:
                log.error(f"Error getting user documents: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        return app
    
    def _is_valid_document(self, filename):
        """Check if file has supported extension."""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.config.supported_extensions
    
    def _is_file_size_valid(self, file_path):
        """Check if file size is within limits."""
        try:
            size = os.path.getsize(file_path)
            return size <= self.config.max_file_size
        except:
            return False
    
    def _read_file_content(self, file_path):
        """Safely read file content."""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            log.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def _emit_to_kafka(self, filename, file_path, source, summary="", sender="System"):
        """Send document metadata to Kafka and log to database."""
        if not self.kafka_producer:
            log.error("Kafka producer not available")
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
            self.kafka_producer.flush(timeout=10)  # Wait up to 10 seconds
            
            # Log successful emission
            self.db.log_processing_step(doc_id, "ingestion", "completed", "Document sent to extraction pipeline")
            
            log.info(f"[Kafka ✅] Sent to topic '{self.config.kafka_topic}': {filename}")
            return metadata
            
        except Exception as e:
            log.error(f"[Kafka ❌] Failed to send {filename}: {e}")
            if 'doc_id' in locals():
                self.db.log_processing_step(doc_id, "ingestion", "failed", str(e))
            return None
    
    def _setup_gmail_auth(self):
        """Setup Gmail authentication."""
        if not self.config.gmail_enabled:
            return None
            
        creds = None
        if os.path.exists(self.config.gmail_token_file):
            creds = Credentials.from_authorized_user_file(self.config.gmail_token_file, self.config.gmail_scopes)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    log.warning(f"Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.config.gmail_credentials_file):
                    log.error(f"Gmail credentials file not found: {self.config.gmail_credentials_file}")
                    return None
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.config.gmail_credentials_file, self.config.gmail_scopes)
                    # Use automatic port selection and better OAuth handling
                    log.info("Starting Gmail OAuth authentication flow...")
                    creds = flow.run_local_server(port=0, prompt='consent')
                    log.info("Gmail OAuth authentication completed successfully")
                except Exception as e:
                    log.error(f"Gmail OAuth authentication failed: {e}")
                    return None
            
            # Save the credentials for next time
            try:
                with open(self.config.gmail_token_file, 'w') as token:
                    token.write(creds.to_json())
                log.info("Gmail credentials saved successfully")
            except Exception as e:
                log.error(f"Failed to save Gmail credentials: {e}")
        
        return creds
    
    def _load_gmail_state(self):
        """Load Gmail processing state (last processed timestamp)."""
        try:
            if os.path.exists(self.config.gmail_state_file):
                with open(self.config.gmail_state_file, 'r') as f:
                    state = json.load(f)
                    return state.get('last_processed_timestamp')
        except Exception as e:
            log.warning(f"Failed to load Gmail state: {e}")
        return None
    
    def _save_gmail_state(self, timestamp):
        """Save Gmail processing state."""
        try:
            state = {'last_processed_timestamp': timestamp}
            with open(self.config.gmail_state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            log.error(f"Failed to save Gmail state: {e}")
    
    def _initialize_gmail_state(self):
        """Initialize Gmail state to current time (to ignore old emails)."""
        current_time = datetime.now().isoformat()
        self._save_gmail_state(current_time)
        log.info("Gmail state initialized - will only process new emails from now on")
    
    def _fetch_gmail_attachments(self, fetch_all=False):
        """Fetch attachments from Gmail.
        
        Args:
            fetch_all (bool): If True, fetch all unread emails. 
                            If False, only fetch emails newer than last processed timestamp.
        """
        """Fetch attachments from Gmail.
        
        Args:
            fetch_all (bool): If True, fetch all unread emails. 
                            If False, only fetch emails newer than last processed timestamp.
        """
        if not self.config.gmail_enabled:
            log.info("Gmail integration disabled")
            return
            
        try:
            creds = self._setup_gmail_auth()
            if not creds:
                log.error("Gmail authentication failed")
                return
                
            service = build('gmail', 'v1', credentials=creds)
            
            # Build query based on fetch_all parameter
            if fetch_all:
                query = 'is:unread has:attachment'
                log.info("Fetching ALL unread emails with attachments...")
            else:
                last_processed = self._load_gmail_state()
                if last_processed:
                    # Convert to Gmail date format (YYYY/MM/DD)
                    try:
                        last_date = datetime.fromisoformat(last_processed.replace('Z', '+00:00'))
                        date_str = last_date.strftime('%Y/%m/%d')
                        query = f'is:unread has:attachment after:{date_str}'
                        log.info(f"Fetching emails newer than {date_str}...")
                    except:
                        query = 'is:unread has:attachment'
                        log.warning("Invalid last processed date, fetching all unread emails")
                else:
                    # First run - initialize state and don't process old emails
                    self._initialize_gmail_state()
                    log.info("First Gmail connection - initialized state, no old emails processed")
                    return
            
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            log.info(f"Found {len(messages)} emails to process")
            
            processed_count = 0
            current_time = datetime.now().isoformat()
            
            for message in messages:
                msg_id = message['id']
                msg = service.users().messages().get(userId='me', id=msg_id).execute()
                
                # Process attachments
                attachments_processed = self._process_gmail_message(service, msg)
                if attachments_processed > 0:
                    processed_count += attachments_processed
                
                # Mark as read
                service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
            
            # Update last processed timestamp
            self._save_gmail_state(current_time)
            
            if processed_count > 0:
                log.info(f"Processed {processed_count} Gmail attachments")
            else:
                log.info("No new Gmail attachments to process")
            
        except Exception as e:
            log.error(f"Gmail processing failed: {e}")
    
    def _process_gmail_message(self, service, message):
        """Process Gmail message and extract attachments.
        
        Returns:
            int: Number of attachments processed
        """
        processed_count = 0
        try:
            msg_id = message['id']
            sender = "Gmail"
            
            # Get sender info
            headers = message['payload'].get('headers', [])
            for header in headers:
                if header['name'] == 'From':
                    sender = header['value']
                    break
            
            # Process parts for attachments
            parts = message['payload'].get('parts', [])
            if not parts:
                parts = [message['payload']]
            
            for part in parts:
                if part.get('filename'):
                    attachment_id = part['body'].get('attachmentId')
                    if attachment_id:
                        attachment = service.users().messages().attachments().get(
                            userId='me',
                            messageId=msg_id,
                            id=attachment_id
                        ).execute()
                        
                        file_data = base64.urlsafe_b64decode(attachment['data'])
                        filename = part['filename']
                        
                        if self._is_valid_document(filename):
                            filepath = os.path.join(self.config.files_dir, filename)
                            
                            # Save file
                            with open(filepath, 'wb') as f:
                                f.write(file_data)
                            
                            if self._is_file_size_valid(filepath):
                                # Emit to Kafka
                                self._emit_to_kafka(
                                    filename,
                                    filepath,
                                    source="gmail",
                                    summary=f"Email attachment from {sender}",
                                    sender=sender
                                )
                                log.info(f"Gmail attachment processed: {filename}")
                                processed_count += 1
                            else:
                                os.remove(filepath)
                                log.warning(f"Gmail attachment too large, skipped: {filename}")
        
        except Exception as e:
            log.error(f"Failed to process Gmail message: {e}")
        
        return processed_count
    
    def _start_gmail_monitor(self):
        """Start Gmail monitoring in background."""
        if not self.config.gmail_enabled:
            return
            
        def gmail_loop():
            log.info("Gmail monitor started")
            while True:
                try:
                    self._fetch_gmail_attachments()
                    time.sleep(self.config.gmail_check_interval)
                except Exception as e:
                    log.error(f"Gmail monitor error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        gmail_thread = threading.Thread(target=gmail_loop, daemon=True)
        gmail_thread.start()
        log.info(f"Gmail monitoring enabled (check interval: {self.config.gmail_check_interval}s)")
    
    def _handle_api_upload(self, request):
        """Handle API file uploads."""
        if 'document' not in request.files:
            return jsonify({'error': 'No document file provided'}), 400

        doc_file = request.files['document']
        metadata_json = request.form.get('metadata', '{}')
        
        try:
            metadata = json.loads(metadata_json)
        except:
            metadata = {}

        if not self._is_valid_document(doc_file.filename):
            return jsonify({'error': 'Invalid document type'}), 400

        filename = secure_filename(doc_file.filename)
        filepath = os.path.join(self.config.files_dir, filename)
        
        try:
            doc_file.save(filepath)
            
            if not self._is_file_size_valid(filepath):
                os.remove(filepath)
                return jsonify({'error': 'File too large'}), 400
            
            # Emit to Kafka
            result_metadata = self._emit_to_kafka(
                filename,
                filepath,
                source="api_upload",
                summary=metadata.get('summary', 'API upload'),
                sender=metadata.get('sender', request.remote_addr or "API")
            )
            
            if result_metadata:
                log.info(f"API upload successful: {filename}")
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
            log.error(f"API upload failed for {filename}: {e}")
            return jsonify({'error': str(e)}), 500
    
    def _start_file_watcher(self):
        """Start file system monitoring."""
        class DocumentHandler(FileSystemEventHandler):
            def __init__(self, ingestor):
                self.ingestor = ingestor
                
            def on_created(self, event):
                if event.is_directory:
                    return
                
                file_path = event.src_path
                filename = os.path.basename(file_path)
                
                if not self.ingestor._is_valid_document(filename):
                    return
                
                # Wait a bit for file to be fully written
                time.sleep(0.5)
                
                # Check if file still exists (it might have been processed already)
                if not os.path.exists(file_path):
                    log.debug(f"File no longer exists, likely already processed: {filename}")
                    return
                
                if not self.ingestor._is_file_size_valid(file_path):
                    try:
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        max_size_mb = self.ingestor.config.max_file_size / (1024 * 1024)
                        log.warning(f"File too large, skipping: {filename} ({file_size_mb:.1f}MB > {max_size_mb:.0f}MB limit)")
                    except FileNotFoundError:
                        log.debug(f"File disappeared during size check: {filename}")
                    return
                
                log.info(f"New document detected: {filename}")
                
                # Emit to Kafka
                self.ingestor._emit_to_kafka(
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
        
        log.info(f"File watcher started monitoring: {self.config.files_dir}")
        return observer
    
    def start_services(self):
        """Start all ingestor services."""
        log.info("Starting Document Ingestor Service...")
        
        # Start file watcher in background
        observer = self._start_file_watcher()
        
        # Start Gmail monitor if enabled
        self._start_gmail_monitor()
        
        try:
            # Start Flask web server
            log.info(f"Starting web server on port {self.config.web_port}...")
            self.flask_app.run(
                host='0.0.0.0', 
                port=self.config.web_port, 
                debug=False,
                threaded=True
            )
        except KeyboardInterrupt:
            log.info("Ingestor service stopped by user.")
        finally:
            if observer:
                observer.stop()
                observer.join()
            if self.kafka_producer:
                self.kafka_producer.close()

def main():
    """Main entry point."""
    ingestor = DocumentIngestor()
    ingestor.start_services()

if __name__ == "__main__":
    main()
