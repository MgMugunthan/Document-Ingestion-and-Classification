"""
Documents Management API - PostgreSQL Version

Provides endpoints for managing classified documents.
Allows users to view, filter, delete, reclassify, and reroute documents.
"""

import os
import json
import shutil
from flask import Blueprint, request, jsonify
from datetime import datetime
import sys

# Add parent directory for database import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.database import db_manager
import logger

log = logger.get_agent_logger("DocumentsAPI")

# Create Blueprint for documents API
documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

@documents_bp.route('/', methods=['GET'])
def get_documents():
    """Get all documents with optional filtering."""
    try:
        # Get query parameters
        document_type = request.args.get('type')
        status = request.args.get('status')
        user_id = request.args.get('user_id')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'upload_time')
        sort_order = request.args.get('sort_order', 'DESC')
        
        log.debug(f"Getting documents for user_id: {user_id}, status: {status}, type: {document_type}")
        
        # Use the database manager to get documents
        documents = db_manager.get_documents(
            user_id=user_id,
            status=status,
            category=document_type
        )
        
        log.debug(f"Raw documents from db_manager: {len(documents) if documents else 0} items")
        
        if not documents:
            documents = []
        
        # Convert to proper format
        documents_list = []
        for doc in documents:
            if isinstance(doc, tuple):
                # Convert tuple to dict based on get_documents return format
                doc_dict = {
                    'id': doc[0],
                    'filename': doc[1],
                    'status': doc[2],
                    'category': doc[3],
                    'confidence': doc[4],
                    'user_id': doc[5] if len(doc) > 5 else None,
                    'upload_time': str(doc[6]) if len(doc) > 6 and doc[6] else None,
                    'final_path': doc[7] if len(doc) > 7 else None
                }
            else:
                # Already a dict
                doc_dict = doc
            
            # Apply search filter
            if search:
                search_lower = search.lower()
                filename = doc_dict.get('filename', '').lower()
                category = doc_dict.get('category', '').lower()
                if search_lower not in filename and search_lower not in category:
                    continue
            
            # Calculate file size if path exists
            file_path = doc_dict.get('final_path')
            if file_path and os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path)
                    if size < 1024:
                        doc_dict['file_size_formatted'] = f"{size} B"
                    elif size < 1024 * 1024:
                        doc_dict['file_size_formatted'] = f"{size / 1024:.1f} KB"
                    else:
                        doc_dict['file_size_formatted'] = f"{size / (1024 * 1024):.1f} MB"
                except:
                    doc_dict['file_size_formatted'] = "Unknown"
            else:
                doc_dict['file_size_formatted'] = "Unknown"
            
            # Map fields for frontend compatibility
            doc_dict['document_id'] = doc_dict.get('id')
            doc_dict['document_name'] = doc_dict.get('filename')
            doc_dict['processing_status'] = doc_dict.get('status')
            doc_dict['classification_type'] = doc_dict.get('category')
            doc_dict['confidence_score'] = doc_dict.get('confidence')
            doc_dict['upload_timestamp'] = doc_dict.get('upload_time')
            doc_dict['routed_path'] = doc_dict.get('final_path')
            
            documents_list.append(doc_dict)
        
        log.debug(f"Formatted documents: {len(documents_list)} items")
        
        # Sort documents
        if sort_by in ['upload_time', 'upload_timestamp', 'filename', 'document_name', 'category', 'classification_type', 'confidence', 'confidence_score', 'status', 'processing_status']:
            reverse = sort_order.upper() == 'DESC'
            documents_list.sort(
                key=lambda x: x.get(sort_by, '') or '',
                reverse=reverse
            )
        
        # Apply pagination
        total_count = len(documents_list)
        start_idx = offset
        end_idx = offset + limit
        paginated_docs = documents_list[start_idx:end_idx]
        
        return jsonify({
            "success": True,
            "data": paginated_docs,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }), 200
        
    except Exception as e:
        log.error(f"Error in get_documents: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@documents_bp.route('/types', methods=['GET'])
def get_document_types():
    """Get all unique document types."""
    try:
        user_id = request.args.get('user_id')
        
        # Get documents from database manager
        documents = db_manager.get_documents(user_id=user_id)
        
        if not documents:
            return jsonify({
                "success": True,
                "data": []
            })
        
        # Count document types
        type_counts = {}
        for doc in documents:
            if isinstance(doc, tuple):
                doc_type = doc[3] if len(doc) > 3 else None  # category field
            else:
                doc_type = doc.get('category') or doc.get('classification_type')
            
            if doc_type:
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        # Convert to list format
        types_list = []
        for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            types_list.append({
                'classification_type': doc_type,
                'count': count
            })
        
        return jsonify({
            "success": True,
            "data": types_list
        })
        
    except Exception as e:
        log.error(f"Error in get_document_types: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@documents_bp.route('/routes', methods=['GET'])
def get_available_routes():
    """Get available routing options from routes.json."""
    try:
        routes_path = os.path.join(os.path.dirname(__file__), '..', 'router', 'routes.json')
        
        with open(routes_path, 'r') as f:
            routes_config = json.load(f)
        
        # Get unique folder destinations
        folders = set()
        for route_type, folder in routes_config.get("routes", {}).items():
            folders.add(folder)
        
        # Add default folders
        folders.add(routes_config.get("default_folder", "others"))
        folders.add(routes_config.get("needs_action_folder", "needs_action"))
        
        return jsonify({
            "success": True,
            "data": {
                "routes": routes_config.get("routes", {}),
                "folders": list(folders),
                "default_folder": routes_config.get("default_folder", "others"),
                "needs_action_folder": routes_config.get("needs_action_folder", "needs_action")
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Functional endpoints for document management
@documents_bp.route('/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a document and its physical file."""
    try:
        # Get document info from database first
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_path, final_path, routed_path 
                FROM documents 
                WHERE document_id = %s
            """, (document_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    "success": False,
                    "error": "Document not found"
                }), 404
            
            file_path, final_path, routed_path = result
            
            # Delete physical files
            import os
            files_to_delete = [file_path]
            if final_path and final_path != file_path:
                files_to_delete.append(final_path)
            if routed_path and routed_path != file_path and routed_path != final_path:
                files_to_delete.append(routed_path)
            
            deleted_files = []
            for file_path_to_delete in files_to_delete:
                if file_path_to_delete and os.path.exists(file_path_to_delete):
                    try:
                        os.remove(file_path_to_delete)
                        deleted_files.append(file_path_to_delete)
                    except OSError as e:
                        log.warning(f"Could not delete file {file_path_to_delete}: {e}")
            
            # Delete from database
            cursor.execute("DELETE FROM documents WHERE document_id = %s", (document_id,))
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": f"Document deleted successfully. Files removed: {len(deleted_files)}"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error deleting document: {str(e)}"
        }), 500

@documents_bp.route('/<document_id>/reroute', methods=['POST'])
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
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_path, final_path, routed_path, original_filename 
                FROM documents 
                WHERE document_id = %s
            """, (document_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    "success": False,
                    "error": "Document not found"
                }), 404
            
            file_path, current_final_path, current_routed_path, original_filename = result
            
            # Load routes configuration
            import os
            import json
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
            source_file = current_final_path or current_routed_path or file_path
            if os.path.exists(source_file):
                shutil.move(source_file, new_file_path)
            
            # Update database
            cursor.execute("""
                UPDATE documents 
                SET final_path = %s, routed_path = %s, updated_at = CURRENT_TIMESTAMP
                WHERE document_id = %s
            """, (new_file_path, new_file_path, document_id))
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": f"Document successfully rerouted to {new_folder}",
                "new_path": new_file_path
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error rerouting document: {str(e)}"
        }), 500

@documents_bp.route('/<document_id>/reclassify', methods=['POST'])
def reclassify_document(document_id):
    """Reclassify a document - simplified version."""
    return jsonify({
        "success": False,
        "error": "Reclassify functionality not yet implemented for PostgreSQL"
    }), 501

@documents_bp.route('/<document_id>/view', methods=['GET'])
def view_document(document_id):
    """View a document - simplified version."""
    return jsonify({
        "success": False,
        "error": "View functionality not yet implemented for PostgreSQL"
    }), 501

@documents_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get document statistics - simplified version."""
    try:
        user_id = request.args.get('user_id')
        documents = db_manager.get_documents(user_id=user_id)
        
        if not documents:
            return jsonify({
                "success": True,
                "data": {
                    "total_documents": 0,
                    "by_status": {},
                    "by_type": {}
                }
            })
        
        # Basic stats
        total = len(documents)
        by_status = {}
        by_type = {}
        
        for doc in documents:
            if isinstance(doc, tuple):
                status = doc[2] if len(doc) > 2 else 'unknown'
                doc_type = doc[3] if len(doc) > 3 else 'unknown'
            else:
                status = doc.get('status', 'unknown')
                doc_type = doc.get('category', 'unknown')
            
            by_status[status] = by_status.get(status, 0) + 1
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
        
        return jsonify({
            "success": True,
            "data": {
                "total_documents": total,
                "by_status": by_status,
                "by_type": by_type
            }
        })
        
    except Exception as e:
        log.error(f"Error in get_stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
