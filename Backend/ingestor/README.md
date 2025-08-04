# Document Ingestor Service

## Quick Start
```bash
python ingestor.py
```

## Structure
- `ingestor.py` - Main ingestor service (combines all functionality)
- `uploads/` - Directory for uploaded documents  
- `web/` - Web interface assets (static files, templates)
- `backup_old_files/` - Archived original files

## Endpoints
- **Web UI**: http://localhost:5000
- **Upload API**: POST http://localhost:5000/api/receive
- **Gmail Fetch (New Only)**: POST http://localhost:5000/api/gmail/fetch
- **Gmail Fetch (All)**: POST http://localhost:5000/api/gmail/fetch-all
- **Gmail Status**: GET http://localhost:5000/api/gmail/status
- **Gmail Reset**: POST http://localhost:5000/api/gmail/reset
- **Status**: GET http://localhost:5000/api/status

## Features
- File system monitoring
- Web file uploads
- API file uploads
- Gmail attachment processing with intelligent controls:
  - **Smart Processing**: Only processes new emails by default (after first connection)
  - **Manual Control**: Fetch old emails only when explicitly requested
  - **State Tracking**: Remembers last processed timestamp
- Kafka message publishing
- Automatic file validation

## Gmail Integration Controls

### Default Behavior (Smart Mode)
- On first connection: Initializes state, ignores all existing emails
- Ongoing monitoring: Only processes emails received after connection
- No old email spam - you're in control!

### Manual Controls
- **Fetch New Only**: `POST /api/gmail/fetch` - Processes only new emails
- **Fetch All**: `POST /api/gmail/fetch-all` - Processes ALL unread emails (including old ones)
- **Check Status**: `GET /api/gmail/status` - Shows connection status and last processed timestamp
- **Reset State**: `POST /api/gmail/reset` - Reset to ignore old emails again

## Configuration
Edit the `IngestorConfig` class in `ingestor.py` to customize:
- Supported file types
- Upload directory
- Kafka settings
- File size limits
- Gmail integration settings

## Gmail Setup (Optional)
1. Create a Google Cloud project
2. Enable Gmail API
3. Download `credentials.json` to the ingestor folder
4. The service will authenticate automatically on first run
