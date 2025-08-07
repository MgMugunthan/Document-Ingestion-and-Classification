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
        
        print(f"Getting documents for user_id: {user_id}, status: {status}, type: {document_type}")
        
        # Use the database manager to get documents
        documents = db_manager.get_documents(
            user_id=user_id,
            status=status,
            category=document_type
        )
        
        print(f"Raw documents from db_manager: {documents}")
        
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
        
        print(f"Formatted documents: {len(documents_list)} items")
        
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
        print(f"Error in get_documents: {str(e)}")
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
        print(f"Error in get_document_types: {str(e)}")
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

# Simplified placeholder endpoints for other functionality
@documents_bp.route('/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a document - simplified version."""
    return jsonify({
        "success": False,
        "error": "Delete functionality not yet implemented for PostgreSQL"
    }), 501

@documents_bp.route('/<document_id>/reroute', methods=['POST'])
def reroute_document(document_id):
    """Reroute a document - simplified version."""
    return jsonify({
        "success": False,
        "error": "Reroute functionality not yet implemented for PostgreSQL"
    }), 501

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
        print(f"Error in get_stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
