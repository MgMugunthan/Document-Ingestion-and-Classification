import psycopg2
import psycopg2.extras

# Database connection
connection_params = {
    'host': 'localhost',
    'port': 5432,
    'database': 'document_system',
    'user': 'postgres',
    'password': '1234567890'
}

try:
    conn = psycopg2.connect(**connection_params)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get all documents
    cursor.execute("SELECT document_id, document_name, uploaded_by, processing_status, upload_timestamp FROM documents ORDER BY upload_timestamp DESC LIMIT 10;")
    documents = cursor.fetchall()
    
    print(f"Found {len(documents)} documents:")
    for doc in documents:
        print(f"- {doc['document_name']} | User: {doc['uploaded_by']} | Status: {doc['processing_status']} | ID: {doc['document_id']}")
    
    # Get unique users
    cursor.execute("SELECT DISTINCT uploaded_by FROM documents;")
    users = cursor.fetchall()
    
    print(f"\nUnique users who uploaded documents:")
    for user in users:
        print(f"- {user['uploaded_by']}")
        
    conn.close()
    
except Exception as e:
    print(f"Database error: {e}")
