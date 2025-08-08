"""
Flask Routes Module

Contains all Flask web routes for the document ingestor service.
"""

import os
import json
import shutil
import psycopg2.extras
from flask import Blueprint, request, jsonify, redirect
from werkzeug.utils import secure_filename
import sys

# Add parent directory for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

def create_routes(ingestor_core, gmail_handler):
    """Create Flask blueprint with all routes."""
    
    routes_bp = Blueprint('ingestor', __name__)
    log = logger.get_agent_logger("IngestorRoutes")
    
    @routes_bp.route('/')
    def index():
        """Simple status page."""
        return """
        <html><head><title>Document Ingestor</title></head>
        <body>
            <h1>Document Ingestor Service</h1>
            <p><strong>Status:</strong>  Running</p>
            <p><strong>Frontend:</strong> <a href="http://localhost:3000">Open App</a></p>
            <hr>
            <h2>API Endpoints:</h2>
            <ul>
                <li><code>POST /api/receive</code> - Upload documents</li>
                <li><code>GET /api/status</code> - Service status</li>
                <li><code>GET /api/document/&lt;id&gt;/status</code> - Document status</li>
                <li><code>GET /api/documents/user/&lt;id&gt;</code> - User documents</li>
                <li><code>POST /api/gmail/*</code> - Gmail integration</li>
            </ul>
        </body></html>
        """
    
    @routes_bp.route('/api/receive', methods=['POST'])
    def api_receive():
        """Handle API file uploads."""
        return ingestor_core.handle_api_upload(request)
    
    @routes_bp.route('/api/debug-form', methods=['POST'])
    def debug_form():
        """Debug endpoint to check form data."""
        form_data = dict(request.form)
        files = list(request.files.keys())
        return jsonify({
            'form_data': form_data,
            'files': files,
            'user_id_from_form': request.form.get('user_id')
        })
    
    @routes_bp.route('/api/status')
    def status():
        """Get service status."""
        return jsonify({
            'status': 'running',
            'service': 'document-ingestor',
            'kafka_connected': ingestor_core.kafka_producer is not None,
            'database_connected': ingestor_core.db is not None,
            'watching_folder': ingestor_core.config.files_dir,
            'supported_types': ingestor_core.config.supported_extensions,
            'gmail_enabled': gmail_handler.is_available(),
            'endpoints': {
                'api_receive': 'POST /api/receive',
                'document_status': 'GET /api/document/<doc_id>/status',
                'user_documents': 'GET /api/documents/user/<user_id>',
                'gmail_fetch_new': 'POST /api/gmail/fetch',
                'gmail_fetch_all': 'POST /api/gmail/fetch-all',
                'gmail_status': 'GET /api/gmail/status',
                'gmail_reset': 'POST /api/gmail/reset',
                'gmail_search': 'POST /api/gmail/search',
                'gmail_process_selected': 'POST /api/gmail/process-selected',
                'gmail_auth_start': 'GET /api/gmail/auth/start',
                'gmail_auth_disconnect': 'POST /api/gmail/auth/disconnect',
                'status': 'GET /api/status'
            }
        })
    
    # Gmail routes
    @routes_bp.route('/api/gmail/fetch', methods=['POST'])
    def gmail_fetch():
        """Manually trigger Gmail attachment fetching."""
        try:
            fetch_all = request.json.get('fetch_all', False) if request.is_json else False
            gmail_handler.fetch_attachments(fetch_all=fetch_all)
            mode = "all emails" if fetch_all else "new emails only"
            return jsonify({
                'status': 'success', 
                'message': f'Gmail fetch completed ({mode})'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @routes_bp.route('/api/gmail/fetch-all', methods=['POST'])
    def gmail_fetch_all():
        """Fetch ALL unread emails with attachments."""
        try:
            gmail_handler.fetch_attachments(fetch_all=True)
            return jsonify({
                'status': 'success', 
                'message': 'All unread Gmail attachments fetched'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @routes_bp.route('/api/gmail/status')
    def gmail_status():
        """Get Gmail integration status."""
        return jsonify(gmail_handler.get_status())
    
    @routes_bp.route('/api/gmail/reset', methods=['POST'])
    def gmail_reset():
        """Reset Gmail state."""
        try:
            gmail_handler.initialize_state()
            return jsonify({
                'status': 'success',
                'message': 'Gmail state reset - will only process new emails from now on'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @routes_bp.route('/api/gmail/search', methods=['POST'])
    def gmail_search():
        """Search Gmail using natural language prompt."""
        try:
            data = request.get_json()
            if not data or 'prompt' not in data:
                return jsonify({'error': 'Prompt required'}), 400
            
            result = gmail_handler.search_by_prompt(data['prompt'])
            return jsonify(result)
            
        except Exception as e:
            log.error(f"Gmail search error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @routes_bp.route('/api/gmail/process-selected', methods=['POST'])
    def gmail_process_selected():
        """Process selected Gmail files."""
        try:
            data = request.get_json()
            if not data or 'file_ids' not in data:
                return jsonify({'error': 'file_ids required'}), 400
            
            result = gmail_handler.process_selected_files(data['file_ids'])
            return jsonify(result)
            
        except Exception as e:
            log.error(f"Gmail processing error: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Gmail Authentication Routes
    @routes_bp.route('/api/gmail/auth/start', methods=['GET'])
    def gmail_auth_start():
        """Start Gmail OAuth authentication flow."""
        if not gmail_handler or not gmail_handler.is_available():
            return jsonify({'error': 'Gmail integration not available'}), 400
        
        try:
            auth_url, error = gmail_handler.get_auth_url()
            if error:
                return jsonify({'error': error}), 400
            
            # Return the auth URL as JSON instead of redirecting
            return jsonify({'auth_url': auth_url})
            
        except Exception as e:
            log.error(f"Gmail OAuth start failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @routes_bp.route('/api/gmail/auth/disconnect', methods=['POST'])
    def gmail_auth_disconnect():
        """Disconnect Gmail integration."""
        if not gmail_handler or not gmail_handler.is_available():
            return jsonify({'error': 'Gmail integration not available'}), 400
        
        try:
            result = gmail_handler.disconnect()
            if result['status'] == 'success':
                log.info(f"Gmail disconnected: {result['message']}")
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            log.error(f"Gmail disconnect failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @routes_bp.route("/api/gmail/auth/callback")
    def gmail_auth_callback():
        """Handle Gmail OAuth callback."""
        if not gmail_handler or not gmail_handler.is_available():
            return """
            <html><body>
                <h2>Gmail integration not available</h2>
                <script>
                    if (window.opener) {
                        window.opener.postMessage({ type: 'gmail_error', error: 'Gmail integration not available' }, '*');
                        window.close();
                    }
                </script>
            </body></html>
            """, 400
        
        try:
            success, result = gmail_handler.handle_auth_callback(request.url)
            
            if success:
                log.info(f"Gmail authorization successful for {result}")
                
                # Now start Gmail monitoring since user has connected
                gmail_handler.start_monitor()
                log.info("Gmail monitoring started after successful authentication")
                
                return redirect("http://localhost:3000/gmail-connected")
            else:
                log.error(f"Gmail OAuth callback failed: {result}")
                return f"""
                <html><body>
                    <h2>OAuth Error</h2>
                    <p>{result}</p>
                    <script>
                        if (window.opener) {{
                            window.opener.postMessage({{ type: 'gmail_error', error: '{result}' }}, '*');
                            window.close();
                        }}
                    </script>
                </body></html>
                """, 500
                
        except Exception as e:
            log.error(f"Gmail OAuth callback failed: {e}")
            return f"""
            <html><body>
                <h2>OAuth Error</h2>
                <p>{str(e)}</p>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{ type: 'gmail_error', error: '{str(e)}' }}, '*');
                        window.close();
                    }}
                </script>
            </body></html>
            """, 500
    
    @routes_bp.route('/api/document/<doc_id>/status', methods=['GET'])
    def get_document_status(doc_id):
        """Get document processing status."""
        try:
            document = ingestor_core.db.get_document_status(doc_id)
            
            if not document:
                return jsonify({'error': 'Document not found'}), 404
                
            doc_dict = dict(document) if hasattr(document, 'keys') else document
            
            # Get processing logs
            with ingestor_core.db.get_connection() as conn:
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
    
    @routes_bp.route('/api/documents/user/<user_id>', methods=['GET'])
    def get_user_documents(user_id):
        """Get all documents for a specific user."""
        try:
            documents = ingestor_core.db.get_user_documents(user_id)
            docs_list = [dict(doc) for doc in documents] if documents else []
            
            return jsonify({
                'user_id': user_id,
                'document_count': len(docs_list),
                'documents': docs_list
            }), 200
            
        except Exception as e:
            log.error(f"Error getting user documents: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @routes_bp.route('/api/documents/all', methods=['GET'])
    def get_all_documents():
        """Debug endpoint to get all documents (temporary)."""
        try:
            with ingestor_core.db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute('''
                    SELECT document_id, original_filename, uploaded_by, processing_status, upload_timestamp 
                    FROM documents 
                    ORDER BY upload_timestamp DESC
                    LIMIT 20
                ''')
                documents = cursor.fetchall()
                docs_list = [dict(doc) for doc in documents] if documents else []
            
            return jsonify({
                'document_count': len(docs_list),
                'documents': docs_list
            }), 200
            
        except Exception as e:
            log.error(f"Error getting all documents: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    # New Document Management Routes
    @routes_bp.route('/api/documents/routes', methods=['GET'])
    def get_available_routes():
        """Get available routing options from routes.json."""
        try:
            # Get the router directory path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(current_dir)
            routes_file = os.path.join(backend_dir, 'router', 'routes.json')
            
            if not os.path.exists(routes_file):
                return jsonify({
                    "success": False,
                    "error": "Routes configuration file not found"
                }), 404
            
            with open(routes_file, 'r') as f:
                routes_config = json.load(f)
            
            return jsonify({
                "success": True,
                "routes": routes_config
            })
            
        except Exception as e:
            log.error(f"Error loading routes: {e}")
            return jsonify({
                "success": False,
                "error": f"Error loading routes: {str(e)}"
            }), 500

    @routes_bp.route('/api/documents/<document_id>', methods=['DELETE'])
    def delete_document(document_id):
        """Delete a document and its physical file."""
        try:
            # Get document info from database first
            with ingestor_core.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT file_path, final_path, original_filename 
                    FROM documents 
                    WHERE document_id = %s
                """, (document_id,))
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({
                        "success": False,
                        "error": "Document not found"
                    }), 404
                
                file_path, final_path, original_filename = result
                
                # Collect all possible file locations to delete
                files_to_delete = []
                
                # Add database paths if they exist
                if file_path:
                    files_to_delete.append(file_path)
                if final_path and final_path != file_path:
                    files_to_delete.append(final_path)
                
                # Search for files in routed_documents directories (same logic as view_document)
                router_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'router', 'routed_documents')
                search_folders = ['needs_action', 'others', 'invoices', 'receipts', 'resumes', 'bills']
                
                for folder in search_folders:
                    folder_path = os.path.join(router_base_path, folder, original_filename)
                    if os.path.exists(folder_path) and folder_path not in files_to_delete:
                        files_to_delete.append(folder_path)
                
                # Also check uploads directory
                uploads_path = os.path.join(os.path.dirname(__file__), 'uploads', original_filename)
                if os.path.exists(uploads_path) and uploads_path not in files_to_delete:
                    files_to_delete.append(uploads_path)
                
                # Delete physical files
                deleted_files = []
                for file_path_to_delete in files_to_delete:
                    if file_path_to_delete and os.path.exists(file_path_to_delete):
                        try:
                            os.remove(file_path_to_delete)
                            deleted_files.append(file_path_to_delete)
                            log.info(f"Deleted file: {file_path_to_delete}")
                        except OSError as e:
                            log.warning(f"Could not delete file {file_path_to_delete}: {e}")
                
                # Delete from database
                cursor.execute("DELETE FROM documents WHERE document_id = %s", (document_id,))
                conn.commit()
                
                log.info(f"Document {document_id} deleted successfully. Files removed: {len(deleted_files)} - {deleted_files}")
                return jsonify({
                    "success": True,
                    "message": f"Document deleted successfully. Files removed: {len(deleted_files)}",
                    "deleted_files": deleted_files
                })
                
        except Exception as e:
            log.error(f"Error deleting document {document_id}: {e}")
            return jsonify({
                "success": False,
                "error": f"Error deleting document: {str(e)}"
            }), 500

    @routes_bp.route('/api/documents/<document_id>/reroute', methods=['POST'])
    def reroute_document(document_id):
        """Reroute a document to a new location."""
        try:
            data = request.get_json()
            route = data.get('route')
            custom_folder = data.get('folder')
            
            if not route and not custom_folder:
                return jsonify({
                    "success": False,
                    "error": "Either route or custom folder must be specified"
                }), 400
            
            # Get current document info
            with ingestor_core.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT file_path, final_path, original_filename 
                    FROM documents 
                    WHERE document_id = %s
                """, (document_id,))
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({
                        "success": False,
                        "error": "Document not found"
                    }), 404
                
                file_path, current_final_path, original_filename = result
                
                # Load routes configuration
                import shutil
                current_dir = os.path.dirname(os.path.abspath(__file__))
                backend_dir = os.path.dirname(current_dir)
                routes_file = os.path.join(backend_dir, 'router', 'routes.json')
                
                with open(routes_file, 'r') as f:
                    routes_config = json.load(f)
                
                # Determine new folder
                if custom_folder:
                    new_folder = custom_folder
                else:
                    # Use predefined routes
                    if route in routes_config.get('routes', {}):
                        new_folder = routes_config['routes'][route]
                    elif route == 'others':
                        new_folder = routes_config.get('default_folder', 'others')
                    elif route == 'needs_action':
                        new_folder = routes_config.get('needs_action_folder', 'needs_action')
                    else:
                        return jsonify({
                            "success": False,
                            "error": "Invalid route specified"
                        }), 400
                
                # Create new path
                routed_documents_dir = os.path.join(backend_dir, 'router', 'routed_documents')
                new_dir = os.path.join(routed_documents_dir, new_folder)
                os.makedirs(new_dir, exist_ok=True)
                
                new_file_path = os.path.join(new_dir, original_filename)
                
                # Move the file
                source_file = current_final_path or file_path
                if os.path.exists(source_file):
                    shutil.move(source_file, new_file_path)
                    log.info(f"Moved file from {source_file} to {new_file_path}")
                else:
                    log.warning(f"Source file {source_file} not found for rerouting")
                
                # Update database
                cursor.execute("""
                    UPDATE documents 
                    SET final_path = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = %s
                """, (new_file_path, document_id))
                conn.commit()
                
                log.info(f"Document {document_id} rerouted to {new_folder}")
                return jsonify({
                    "success": True,
                    "message": f"Document successfully rerouted to {new_folder}",
                    "new_path": new_file_path
                })
                
        except Exception as e:
            log.error(f"Error rerouting document {document_id}: {e}")
            return jsonify({
                "success": False,
                "error": f"Error rerouting document: {str(e)}"
            }), 500

    @routes_bp.route('/api/documents/<document_id>/reclassify', methods=['POST'])
    def reclassify_document(document_id):
        """Reclassify a document and automatically reroute it."""
        try:
            # Get request data
            data = request.get_json()
            if not data or 'new_classification' not in data:
                return jsonify({
                    "success": False,
                    "error": "new_classification is required"
                }), 400
                
            new_classification = data['new_classification'].strip().lower()
            if not new_classification:
                return jsonify({
                    "success": False,
                    "error": "new_classification cannot be empty"
                }), 400
            
            with ingestor_core.db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Get document details
                cursor.execute("""
                    SELECT original_filename, file_path, final_path, classification_type
                    FROM documents 
                    WHERE document_id = %s
                """, (document_id,))
                document = cursor.fetchone()
                
                if not document:
                    return jsonify({
                        "success": False,
                        "error": "Document not found"
                    }), 404
                
                original_filename = document['original_filename']
                file_path = document['file_path']
                current_final_path = document['final_path']
                old_classification = document['classification_type']
                
                # Load routes configuration
                backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                routes_file = os.path.join(backend_dir, 'router', 'routes.json')
                
                try:
                    with open(routes_file, 'r') as f:
                        routes_config = json.load(f)
                except:
                    # Fallback configuration
                    routes_config = {
                        "routes": {"resume": "resumes", "cv": "resumes", "invoice": "invoices", "receipt": "receipts", "bill": "bills"},
                        "default_folder": "others",
                        "needs_action_folder": "needs_action"
                    }
                
                # Determine the new folder based on the new classification
                document_routes = routes_config.get('routes', {})
                if new_classification in document_routes:
                    new_folder = document_routes[new_classification]
                elif new_classification == 'others':
                    new_folder = routes_config.get('default_folder', 'others')
                elif new_classification == 'needs_action':
                    new_folder = routes_config.get('needs_action_folder', 'needs_action')
                else:
                    new_folder = routes_config.get('default_folder', 'others')
                
                # Create new path
                routed_documents_dir = os.path.join(backend_dir, 'router', 'routed_documents')
                new_dir = os.path.join(routed_documents_dir, new_folder)
                os.makedirs(new_dir, exist_ok=True)
                
                new_file_path = os.path.join(new_dir, original_filename)
                
                # Move the file if it exists and needs to be moved
                source_file = current_final_path or file_path
                moved_file = False
                if os.path.exists(source_file):
                    # Only move if the destination is different
                    if os.path.abspath(source_file) != os.path.abspath(new_file_path):
                        shutil.move(source_file, new_file_path)
                        moved_file = True
                        log.info(f"Moved file from {source_file} to {new_file_path}")
                    else:
                        log.info(f"File already in correct location: {new_file_path}")
                else:
                    log.warning(f"Source file {source_file} not found for reclassification")
                
                # Update database with new classification and path
                cursor.execute("""
                    UPDATE documents 
                    SET classification_type = %s, 
                        final_path = %s, 
                        updated_at = CURRENT_TIMESTAMP,
                        classification_method = 'Manual Reclassification',
                        classification_confidence = '1.0000'
                    WHERE document_id = %s
                """, (new_classification, new_file_path, document_id))
                conn.commit()
                
                log.info(f"Document {document_id} reclassified from '{old_classification}' to '{new_classification}' and routed to '{new_folder}'")
                
                message = f"Document successfully reclassified as '{new_classification}' and routed to '{new_folder}' folder"
                if moved_file:
                    message += f". File moved to new location."
                
                return jsonify({
                    "success": True,
                    "message": message,
                    "new_classification": new_classification,
                    "new_folder": new_folder,
                    "new_path": new_file_path
                })
                
        except Exception as e:
            log.error(f"Error reclassifying document {document_id}: {e}")
            return jsonify({
                "success": False,
                "error": f"Error reclassifying document: {str(e)}"
            }), 500

    @routes_bp.route('/api/documents/review', methods=['GET'])
    def get_documents_for_review():
        """Get documents that need review (status: needs_action)."""
        try:
            with ingestor_core.db.get_connection() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Get documents with needs_action status
                cur.execute("""
                    SELECT 
                        document_id,
                        original_filename,
                        uploaded_by,
                        file_size,
                        classification_type,
                        COALESCE(classification_confidence, 0) AS classification_confidence,
                        classification_method,
                        processing_status,
                        final_path,
                        created_at,
                        updated_at,
                        file_extension
                    FROM documents 
                    WHERE processing_status = 'needs_action' 
                    ORDER BY created_at DESC
                """)
                
                documents = cur.fetchall()
                
                # Convert to list of dicts with proper formatting
                result = []
                for doc in documents:
                    doc_dict = dict(doc)
                    # Format for frontend compatibility
                    doc_dict['user_id'] = doc_dict.pop('uploaded_by')
                    doc_dict['document_classification'] = doc_dict.pop('classification_type') 
                    doc_dict['status'] = doc_dict.pop('processing_status')
                    doc_dict['file_type'] = doc_dict.pop('file_extension') or 'unknown'
                    doc_dict['upload_method'] = 'API'  # Add default upload method
                    
                    # Convert datetime objects to ISO strings if they exist
                    if doc_dict.get('created_at'):
                        doc_dict['created_at'] = doc_dict['created_at'].isoformat()
                    if doc_dict.get('updated_at'):
                        doc_dict['updated_at'] = doc_dict['updated_at'].isoformat()
                    # Ensure confidence is a float (handles Decimal and None)
                    try:
                        doc_dict['classification_confidence'] = float(doc_dict.get('classification_confidence') or 0)
                    except Exception:
                        doc_dict['classification_confidence'] = 0.0
                    
                    result.append(doc_dict)
                
                return jsonify({
                    "success": True,
                    "documents": result,
                    "count": len(result)
                })
                
        except Exception as e:
            log.error(f"Error fetching needs action documents: {e}")
            return jsonify({
                "success": False,
                "error": f"Error fetching documents: {str(e)}"
            }), 500

    @routes_bp.route('/api/documents/needsaction', methods=['GET'])
    def get_needs_action_documents():
        """Get documents that need review (status: needs_action)."""
        try:
            with ingestor_core.db.get_connection() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Get documents with needs_action status
                cur.execute("""
                    SELECT 
                        document_id,
                        original_filename,
                        uploaded_by as user_id,
                        'API' as upload_method,
                        file_size,
                        classification_type as document_classification,
                        classification_confidence,
                        classification_method,
                        processing_status as status,
                        final_path,
                        created_at,
                        updated_at,
                        file_extension as file_type
                    FROM documents 
                    WHERE processing_status = 'needs_action' 
                    ORDER BY created_at DESC
                """)
                
                documents = cur.fetchall()
                
                # Convert to list of dicts with proper formatting
                result = []
                for doc in documents:
                    doc_dict = dict(doc)
                    # Convert datetime objects to ISO strings if they exist
                    if doc_dict.get('created_at'):
                        doc_dict['created_at'] = doc_dict['created_at'].isoformat()
                    if doc_dict.get('updated_at'):
                        doc_dict['updated_at'] = doc_dict['updated_at'].isoformat()
                    # Convert Decimal to float for confidence
                    if doc_dict.get('classification_confidence'):
                        doc_dict['classification_confidence'] = float(doc_dict['classification_confidence'])
                    result.append(doc_dict)
                
                return jsonify({
                    "success": True,
                    "documents": result,
                    "count": len(result)
                })
                
        except Exception as e:
            log.error(f"Error fetching needs action documents: {e}")
            return jsonify({
                "success": False,
                "error": f"Error fetching documents: {str(e)}"
            }), 500

    @routes_bp.route('/api/documents/<document_id>/view', methods=['GET'])
    def view_document(document_id):
        """Get document file for viewing."""
        try:
            with ingestor_core.db.get_connection() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Get document info
                cur.execute("""
                    SELECT 
                        document_id,
                        original_filename,
                        final_path,
                        file_path,
                        file_extension AS file_type,
                        file_size
                    FROM documents 
                    WHERE document_id = %s
                """, (document_id,))
                
                document = cur.fetchone()
                
                if not document:
                    return jsonify({
                        "success": False,
                        "error": "Document not found"
                    }), 404
                
                # Try multiple file paths
                file_path = None
                search_paths = []
                
                # Add configured paths if they exist
                if document['final_path']:
                    search_paths.append(document['final_path'])
                if document['file_path']:
                    search_paths.append(document['file_path'])
                    
                # Add ingestor uploads directory as fallback
                uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
                uploads_path = os.path.join(uploads_dir, document['original_filename'])
                search_paths.append(uploads_path)
                
                # Add router routed documents directories
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                routed_base = os.path.join(backend_dir, 'router', 'routed_documents')
                possible_folders = ['needs_action', 'Needs_Action', 'others', 'invoices', 'receipts', 'resumes', 'bills']
                for folder in possible_folders:
                    routed_path = os.path.join(routed_base, folder, document['original_filename'])
                    search_paths.append(routed_path)
                
                # Find the first existing file
                for path in search_paths:
                    if path and os.path.exists(path):
                        file_path = path
                        break
                
                if not file_path:
                    log.warning(f"File not found for document {document_id}. Searched: {search_paths}")
                    return jsonify({
                        "success": False,
                        "error": "Document file not found on disk"
                    }), 404
                
                return jsonify({
                    "success": True,
                    "document": dict(document),
                    "file_path": file_path,
                    "view_url": f"/api/documents/{document_id}/download"
                })
                
        except Exception as e:
            log.error(f"Error viewing document {document_id}: {e}")
            return jsonify({
                "success": False,
                "error": f"Error viewing document: {str(e)}"
            }), 500

    from flask import send_file

    @routes_bp.route('/api/documents/<document_id>/download', methods=['GET'])
    def download_document(document_id):
        """Download document file."""
        try:
            with ingestor_core.db.get_connection() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Get document info
                cur.execute("""
                    SELECT 
                        document_id,
                        original_filename,
                        final_path,
                        file_path,
                        file_extension AS file_type
                    FROM documents 
                    WHERE document_id = %s
                """, (document_id,))
                
                document = cur.fetchone()
                
                if not document:
                    return jsonify({
                        "success": False,
                        "error": "Document not found"
                    }), 404
                
                # Try multiple file paths
                file_path = None
                search_paths = []
                
                # Add configured paths if they exist
                if document['final_path']:
                    search_paths.append(document['final_path'])
                if document['file_path']:
                    search_paths.append(document['file_path'])
                    
                # Add ingestor uploads directory as fallback
                uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
                uploads_path = os.path.join(uploads_dir, document['original_filename'])
                search_paths.append(uploads_path)
                
                # Add router routed documents directories
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                routed_base = os.path.join(backend_dir, 'router', 'routed_documents')
                possible_folders = ['needs_action', 'Needs_Action', 'others', 'invoices', 'receipts', 'resumes', 'bills']
                for folder in possible_folders:
                    routed_path = os.path.join(routed_base, folder, document['original_filename'])
                    search_paths.append(routed_path)
                
                # Find the first existing file
                for path in search_paths:
                    if path and os.path.exists(path):
                        file_path = path
                        break
                
                if not file_path:
                    log.warning(f"File not found for document {document_id}. Searched: {search_paths}")
                    return jsonify({
                        "success": False,
                        "error": "Document file not found on disk"
                    }), 404
                
                # Send file for download
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=document['original_filename']
                )
                
        except Exception as e:
            log.error(f"Error downloading document {document_id}: {e}")
            return jsonify({
                "success": False,
                "error": f"Error downloading document: {str(e)}"
            }), 500

    return routes_bp
