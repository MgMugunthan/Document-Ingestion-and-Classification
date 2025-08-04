import os
import json
import uuid
import shutil
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import sqlite3
import sys
from kafka import KafkaProducer

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

# Get a dedicated logger for the API service
log = logger.get_agent_logger("API")

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'ingestor', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'documents.db')

def init_database():
    """Initialize the documents database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            document_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            file_extension TEXT,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processing_status TEXT DEFAULT 'uploaded',
            classification_type TEXT,
            confidence_score REAL,
            extracted_text TEXT,
            routed_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    log.info("Documents database initialized successfully")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """Handle document upload"""
    try:
        # Check if file is present
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
            
        files = request.files.getlist('files')
        user_id = request.form.get('user_id', 'anonymous')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
            
        uploaded_documents = []
        
        for file in files:
            if file and allowed_file(file.filename):
                # Generate unique document ID
                document_id = str(uuid.uuid4())
                
                # Secure filename
                filename = secure_filename(file.filename)
                if not filename:
                    filename = f"document_{document_id}"
                    
                # Create upload directory if not exists
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # Save file
                file_path = os.path.join(UPLOAD_FOLDER, f"{document_id}_{filename}")
                file.save(file_path)
                
                # Get file info
                file_size = os.path.getsize(file_path)
                file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                # Save to database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO documents 
                    (document_id, user_id, document_name, file_path, file_size, file_extension, processing_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (document_id, user_id, filename, file_path, file_size, file_extension, 'uploaded'))
                conn.commit()
                conn.close()
                
                # Send to Kafka for processing (ingestion)
                try:
                    producer = KafkaProducer(
                        bootstrap_servers='localhost:9092',
                        value_serializer=lambda v: json.dumps(v).encode('utf-8')
                    )
                    
                    # Create message for ingestor
                    kafka_message = {
                        "document_id": document_id,
                        "document_name": filename,
                        "path": file_path,
                        "size": file_size,
                        "file_extension": file_extension,
                        "upload_timestamp": datetime.now().isoformat(),
                        "user_id": user_id
                    }
                    
                    # Send to doc.uploaded topic for ingestor
                    producer.send("doc.uploaded", value=kafka_message)
                    producer.flush()
                    log.info(f"Document sent to Kafka for processing: {document_id}")
                    
                except Exception as kafka_error:
                    log.error(f"Failed to send to Kafka: {str(kafka_error)}")
                    # Continue without Kafka for now - you can enable this in production
                
                uploaded_documents.append({
                    'document_id': document_id,
                    'document_name': filename,
                    'file_size': file_size,
                    'file_extension': file_extension,
                    'status': 'uploaded'
                })
                
                log.info(f"Document uploaded successfully: {document_id} - {filename}")
            else:
                log.warning(f"Invalid file type or empty file: {file.filename}")
                
        return jsonify({
            'message': f'{len(uploaded_documents)} files uploaded successfully',
            'documents': uploaded_documents
        }), 200
        
    except Exception as e:
        log.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/documents/status/<document_id>', methods=['GET'])
def get_document_status(document_id):
    """Get document processing status"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE document_id = ?', (document_id,))
        document = cursor.fetchone()
        conn.close()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
            
        return jsonify({
            'document_id': document[1],
            'document_name': document[3],
            'processing_status': document[8],
            'classification_type': document[9],
            'confidence_score': document[10],
            'upload_timestamp': document[7]
        }), 200
        
    except Exception as e:
        log.error(f"Status check error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/documents/list', methods=['GET'])
def list_documents():
    """List user documents"""
    try:
        user_id = request.args.get('user_id', 'anonymous')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT document_id, document_name, upload_timestamp, processing_status, 
                   classification_type, confidence_score, file_size
            FROM documents 
            WHERE user_id = ? 
            ORDER BY upload_timestamp DESC 
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        
        documents = cursor.fetchall()
        conn.close()
        
        document_list = []
        for doc in documents:
            document_list.append({
                'document_id': doc[0],
                'document_name': doc[1],
                'upload_timestamp': doc[2],
                'processing_status': doc[3],
                'classification_type': doc[4] or 'Pending',
                'confidence_score': doc[5] or 0,
                'file_size': doc[6]
            })
            
        return jsonify({
            'documents': document_list,
            'total': len(document_list)
        }), 200
        
    except Exception as e:
        log.error(f"List documents error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/documents/update-status', methods=['POST'])
def update_document_status():
    """Update document processing status (called by processing services)"""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        status = data.get('status')
        classification_type = data.get('classification_type')
        confidence_score = data.get('confidence_score')
        extracted_text = data.get('extracted_text')
        routed_path = data.get('routed_path')
        
        if not document_id or not status:
            return jsonify({'error': 'Document ID and status are required'}), 400
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update document
        cursor.execute('''
            UPDATE documents 
            SET processing_status = ?, classification_type = ?, confidence_score = ?, 
                extracted_text = ?, routed_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE document_id = ?
        ''', (status, classification_type, confidence_score, extracted_text, routed_path, document_id))
        
        conn.commit()
        conn.close()
        
        log.info(f"Document status updated: {document_id} - {status}")
        return jsonify({'message': 'Status updated successfully'}), 200
        
    except Exception as e:
        log.error(f"Status update error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    log.info("API service starting...")
    init_database()
    app.run(host='0.0.0.0', port=5002, debug=True)
