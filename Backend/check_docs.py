import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database.database import db_manager

try:
    # Get all documents using the database manager
    documents = db_manager.get_documents()
    
    if not documents:
        print("✅ Database is clean - No documents found.")
        print("🚀 System is ready for fresh start!")
    else:
        print(f"⚠️  Found {len(documents)} test documents in database.")
        response = input("🧹 Clear all test documents? (yes/no): ").lower()
        if response == 'yes' or response == 'y':
            # Clear all documents
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM documents")
                cursor.execute("DELETE FROM processing_logs")
                conn.commit()
            print("✅ Database cleared successfully!")
            print("🚀 System is ready for fresh start!")
        else:
            print("📊 Database cleanup skipped.")
    
    print(f"\n� Database connection: ✅ Working")
    print(f"🔧 System status: ✅ Ready")
        
except Exception as e:
    print(f"❌ Database error: {e}")
    print("💡 Make sure PostgreSQL is running and accessible.")