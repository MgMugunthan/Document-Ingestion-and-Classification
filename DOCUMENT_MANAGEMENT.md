# Document Management System

## Overview

The document management system now includes comprehensive frontend and backend integration for managing classified documents with advanced filtering, routing, and administrative controls.

## Features

### 🔄 **Dynamic Document Routing** (`routes.json`)
- **Controlled folder creation**: Only predefined document types create folders
- **Smart routing logic**: 
  - High confidence + mapped type → specific folder
  - High confidence + unmapped type → `others` folder  
  - Low confidence → `needs_action` folder
- **Configurable confidence threshold**: Default 70%

### 📁 **Predefined Routes**
```json
{
  "resume": "resumes",
  "cv": "resumes", 
  "receipt": "receipts",
  "invoice": "invoices",
  "bill": "bills"
}
```

### 🎛️ **Frontend Document Management**
- **Advanced filtering**: By type, status, date, confidence
- **Search functionality**: Search by document name or classification
- **Sorting**: Multiple sort options with ascending/descending order
- **Pagination**: Handle large document collections efficiently

### ⚡ **Document Actions**
- **👁️ View**: Detailed document information and metadata
- **🗂️ Reroute**: Move documents to different folders or routes
- **🏷️ Reclassify**: Change document classification type
- **🗑️ Delete**: Remove documents and associated files

## API Endpoints

### Documents API (`/api/documents`)

#### Get Documents
```
GET /api/documents
Query Parameters:
  - type: Filter by document type
  - status: Filter by processing status
  - search: Search in document names
  - sort_by: Sort field (upload_timestamp, document_name, etc.)
  - sort_order: ASC or DESC
  - limit: Number of results per page
  - offset: Pagination offset
```

#### Document Actions
```
GET /api/documents/types          # Get all document types
GET /api/documents/routes         # Get available routing options
GET /api/documents/stats          # Get document statistics
GET /api/documents/{id}/view      # View document details
DELETE /api/documents/{id}        # Delete document
POST /api/documents/{id}/reroute  # Reroute document
POST /api/documents/{id}/reclassify  # Reclassify document
```

## Router Configuration

### File Structure
```
Backend/router/
├── router.py           # Main router with dynamic config loading
├── routes.json         # Configuration file for routing rules
└── routed_documents/   # Output folder for routed documents
```

### Routing Logic
1. **Load configuration** from `routes.json` for each document
2. **Check confidence** against threshold (default: 0.7)
3. **Route decision**:
   - Low confidence → `needs_action` folder
   - High confidence + mapped type → specific folder
   - High confidence + unmapped type → `others` folder

### Configuration Management
```json
{
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
```

## Frontend Pages

### Documents Management (`/documents`)
- **Comprehensive filtering and search**
- **Real-time data from backend API**
- **Action buttons for each document**
- **Modal dialogs for detailed operations**
- **Responsive design with pagination**

### Key Features:
- **Status badges** with color coding
- **Confidence scores** with visual indicators  
- **File size formatting** (B, KB, MB)
- **Date formatting** for upload and update times
- **Batch operations** support

## Usage Examples

### Rerouting a Document
1. Click the **Route** button (🗂️) on any document
2. Choose from:
   - **Predefined routes**: resume → resumes, invoice → invoices
   - **Custom folder**: Enter any folder name
3. Document is moved and database updated

### Adding New Routes
Edit `Backend/router/routes.json`:
```json
{
  "routes": {
    "contract": "contracts",     // Add new route
    "report": "reports"          // Add another route
  }
}
```
Router automatically picks up changes on next document processing.

### Filtering Documents
- **By Type**: Select from dropdown of existing types
- **By Status**: uploaded, extracted, classified, routed, error
- **By Search**: Document name or classification text
- **By Date**: Sort by upload date (newest/oldest first)

## Security & Permissions
- **Authentication required**: All endpoints protected
- **User-specific data**: Documents filtered by user access
- **Safe file operations**: Copy-first approach to prevent file locking
- **Input validation**: All API inputs validated and sanitized

## Error Handling
- **Database connection failures**: Graceful fallbacks
- **File system errors**: Retry mechanisms with exponential backoff
- **Invalid configurations**: Default values with logging
- **Frontend errors**: User-friendly toast notifications

## Performance Optimizations
- **Pagination**: Large document sets handled efficiently
- **Lazy loading**: Documents loaded on-demand
- **Debounced search**: Reduces API calls during typing
- **Caching**: Document types and routes cached
- **Optimized queries**: Database indexes for common filters

## Future Enhancements
- **Bulk operations**: Select multiple documents for batch actions
- **Document preview**: View document content inline
- **Advanced search**: Full-text search within document content
- **Audit logging**: Track all document operations
- **File versioning**: Keep history of document changes
- **Export functionality**: Download filtered document lists
