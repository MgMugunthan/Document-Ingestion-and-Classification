import psycopg2
import psycopg2.extras
from contextlib import contextmanager
import os
from datetime import datetime
import logging
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger
log = logger.get_agent_logger("Database")
class DatabaseManager:
    def __init__(self):
        self.connection_params={
            'host':'localhost',
            'port': 5432,
            'database': 'document_system',
            'user':'postgres',
            'password':'1234567890'
        }

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn=psycopg2.connect(**self.connection_params)
            yield conn
        except Exception as e:
            log.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()

            raise
        finally:
            if conn:
                conn.close()
    
    def _create_database(self):
        try:
            temp_params=self.connection_params.copy()
            temp_params['database']= 'postgres'
            conn = psycopg2.connect(**temp_params)
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 1 FROM  pg_catalog.pg_database
            WHERE datname=%s
            """, (self.connection_params['database'],))
            if not cursor.fetchone():
                database_name=self.connection_params['database']
                cursor.execute(f"CREATE DATABASE {database_name}")
                log.info(f"Database '{database_name}' created")
            else:
                log.info(f"Database '{self.connection_params['database']}' already  exists")
            cursor.close()
            conn.close()
        except Exception as e:
            log.error(f"Database creation error:{e}")
            raise
    def initialize_database(self):
        try:
            self._create_database()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        user_type VARCHAR(50) NOT NULL,
                        department VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        document_id VARCHAR(100) UNIQUE NOT NULL,
                        original_filename VARCHAR(255) NOT NULL,
                        file_path VARCHAR(500) NOT NULL,
                        file_size BIGINT NOT NULL,
                        file_extension VARCHAR(10),
                        uploaded_by VARCHAR(100),
                        upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processing_status VARCHAR(50) DEFAULT 'uploaded',
                        classification_type VARCHAR(100),
                        classification_confidence DECIMAL(5,4),
                        classification_method VARCHAR(100),
                        final_path VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processing_logs (
                        id SERIAL PRIMARY KEY,
                        document_id VARCHAR(100),
                        stage VARCHAR(50) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        message TEXT,
                        processing_time_ms INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                log.info(f"Database tables created successfully")
        except Exception as e:
            log.error(f"Database initialization error: {e}")
            raise
    def insert_document(self, doc_data):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO documents (
                        document_id, original_filename, file_path, file_size, 
                        file_extension, uploaded_by, processing_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    doc_data['document_id'],
                    doc_data['original_filename'],
                    doc_data['file_path'],
                    doc_data['file_size'],
                    doc_data.get('file_extension', ''),
                    doc_data.get('uploaded_by', 'unknown'),
                    'uploaded'
                ))
                conn.commit()
                log.info(f"Document inserted: {doc_data['document_id']}")
        except Exception as e:
            log.error(f"Error inserting document: {e}")
            raise
    def update_document_status(self, doc_id, status, classification_data=None):
        try:
            with self.get_connection() as conn:
                cursor= conn.cursor()
                if classification_data:
                    cursor.execute('''
                        UPDATE documents SET 
                            processing_status = %s,
                            classification_type = %s,
                            classification_confidence = %s,
                            classification_method = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE document_id = %s
                    ''', (
                        status,
                        classification_data.get('document_type'),
                        classification_data.get('confidence'),
                        classification_data.get('classification_by'),
                        doc_id
                    ))
                else:
                    cursor.execute('''
                        UPDATE documents SET 
                            processing_status = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE document_id = %s
                    ''', (status, doc_id))
                conn.commit()
                log.info(f"Document status updated: {doc_id} -> {status}")
        except Exception as e:
            log.error(f"Error updating document status: {e}")
            raise
    def log_processing_step(self, doc_id, stage, status, message=None, processing_time=None):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO processing_logs (
                        document_id, stage, status, message, processing_time_ms
                    ) VALUES (%s, %s, %s, %s, %s)
                ''', (doc_id, stage, status, message, processing_time))
                conn.commit()
        except Exception as e:
            log.error(f"Error logging processing step: {e}")
    def get_document_status(self, doc_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                    SELECT * FROM documents WHERE document_id = %s
                ''', (doc_id,))
                return cursor.fetchone()
        except Exception as e:
            log.error(f"Error getting document status: {e}")
            return None
    def get_user_documents(self, user_id):
        try: 
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                    SELECT * FROM documents 
                    WHERE uploaded_by = %s 
                    ORDER BY upload_timestamp DESC
                ''', (user_id,))
                return cursor.fetchall()
        except Exception as e:
            log.error(f"Error getting user documents: {e}")
            return []

    def update_document_final_path(self, doc_id, final_path, status="routed"):
        """Update document final path and status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE documents SET 
                        final_path = %s,
                        processing_status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = %s
                ''', (final_path, status, doc_id))
                conn.commit()
                log.info(f"Document final path updated: {doc_id} -> {final_path}")
        except Exception as e:
            log.error(f"Error updating document final path: {e}")
            raise
db_manager = DatabaseManager()
if __name__ == "__main__":
    try:
        db_manager.initialize_database()
        log.info("Database setup completed successfully!")
    except Exception as e:
        log.error(f"Database setup failed: {e}")
