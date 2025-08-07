"""
Flask Routes Module

Contains all Flask web routes for the document ingestor service.
"""

import os
import json
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
    
    return routes_bp
