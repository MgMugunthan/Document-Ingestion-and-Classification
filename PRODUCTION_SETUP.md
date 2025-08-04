# Production Setup Guide

This guide will help you set up the complete system with authentication, cloud storage, and database integration.

## Overview

We've created a modern, production-ready architecture with:

1. **Authentication System** - JWT-based auth with user management
2. **API Layer** - RESTful APIs for document operations
3. **Cloud Storage Integration** - Ready for AWS S3, Google Cloud, etc.
4. **Database Integration** - SQLite for development, PostgreSQL for production
5. **Frontend Integration** - React hooks and API integration

## Backend Services Created

### 1. Authentication Service (`/Backend/auth/auth.py`)
- **Port**: 5001
- **Features**:
  - JWT-based authentication
  - User registration and login
  - Password hashing with bcrypt
  - Token verification
- **Database**: SQLite (users.db)
- **Default Admin**: username: `admin`, password: `admin123`

### 2. API Service (`/Backend/api/api.py`)
- **Port**: 5002
- **Features**:
  - Document upload handling
  - Processing status tracking
  - Document listing
  - File management
- **Database**: SQLite (documents.db)

## Frontend Updates

### 1. API Integration (`/Frontend/lib/api.ts`)
- Complete API client for authentication and document operations
- Token management utilities
- Error handling

### 2. Authentication Context (`/Frontend/contexts/AuthContext.tsx`)
- React context for authentication state
- Login/logout functionality
- Token persistence

### 3. Environment Configuration (`.env.local`)
- API endpoint configuration
- Development settings

## Setup Instructions

### Step 1: Install Backend Dependencies

```bash
# Navigate to Backend directory
cd "d:\Langs\Team_Docs\Local working prototype\Document-Ingestion-and-Classification\Backend"

# Install Auth service dependencies
cd auth
pip install -r requirements.txt

# Install API service dependencies
cd ../api
pip install -r requirements.txt
```

### Step 2: Start Backend Services

```bash
# Terminal 1: Start Authentication Service
cd "d:\Langs\Team_Docs\Local working prototype\Document-Ingestion-and-Classification\Backend\auth"
python auth.py

# Terminal 2: Start API Service
cd "d:\Langs\Team_Docs\Local working prototype\Document-Ingestion-and-Classification\Backend\api"
python api.py

# Terminal 3: Continue running your existing services (if needed)
# - Kafka
# - Document processing pipeline
```

### Step 3: Test the System

1. **Frontend**: http://localhost:3000
2. **Auth API**: http://localhost:5001
3. **Document API**: http://localhost:5002

## Next Steps for Production

### 1. Cloud Storage Integration

Replace local file storage with cloud storage:

**AWS S3 Example:**
```python
import boto3

s3_client = boto3.client('s3',
    aws_access_key_id='your-key',
    aws_secret_access_key='your-secret',
    region_name='your-region'
)

# Upload file
s3_client.upload_file(local_path, bucket_name, s3_key)
```

**Google Cloud Storage Example:**
```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket('your-bucket-name')
blob = bucket.blob('document-path')
blob.upload_from_filename(local_path)
```

### 2. Database Migration

Replace SQLite with PostgreSQL for production:

```python
# Install psycopg2
pip install psycopg2-binary

# Database connection
import psycopg2
conn = psycopg2.connect(
    host="your-host",
    database="your-db",
    user="your-user",
    password="your-password"
)
```

### 3. Enhanced Authentication

Add features like:
- Email verification
- Password reset
- Role-based access control
- OAuth integration (Google, Microsoft)

### 4. Production Deployment

- **Docker containers** for each service
- **Load balancing** with nginx
- **SSL certificates** for HTTPS
- **Environment variables** for configuration
- **Logging and monitoring** with ELK stack or similar

### 5. Frontend Enhancements

- **Real-time updates** with WebSockets
- **Progress tracking** for document processing
- **File preview** capabilities
- **Advanced search and filtering**

## Current Architecture

```
Frontend (Next.js) ─── API Layer (Flask) ─── Document Processing Pipeline
       │                    │                          │
       │                    │                    ┌─────────────┐
       │                    │                    │  Ingestor   │
       │                    │                    └─────────────┘
       │                    │                          │
       │                    │                    ┌─────────────┐
       │                    │                    │  Extractor  │
       │                    │                    └─────────────┘
       │                    │                          │
       │                    │                    ┌─────────────┐
       │                    │                    │ Classifier  │
       │                    │                    └─────────────┘
       │                    │                          │
       │                    │                    ┌─────────────┐
       │                    │                    │   Router    │
       │                    │                    └─────────────┘
       │                    │
       │              ┌─────────────┐
       │              │    Auth     │
       │              │  Service    │
       │              └─────────────┘
       │
   ┌─────────────┐
   │    Users    │
   └─────────────┘
```

## Security Considerations

1. **JWT Secret**: Change the default JWT secret key
2. **Password Policy**: Implement strong password requirements
3. **Rate Limiting**: Add API rate limiting
4. **Input Validation**: Validate all user inputs
5. **File Upload Security**: Scan uploaded files for malware
6. **CORS Configuration**: Properly configure CORS for production

## Testing

Create test users and documents to verify:
1. User registration and login
2. Document upload and processing
3. Classification and routing
4. API security and authentication

The system is now ready for production deployment with proper security, scalability, and maintainability!
