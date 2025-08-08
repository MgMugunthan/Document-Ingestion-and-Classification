import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger
from database.database import db_manager

# Import API blueprints
from documents_api import documents_bp

# Get a dedicated logger for the API service
log = logger.get_agent_logger("API")

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(documents_bp)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with db_manager.get_connection() as conn:
            return jsonify({
                "service": "Documents API",
                "status": "healthy",
                "database": "connected",
                "timestamp": __import__('datetime').datetime.utcnow().isoformat()
            })
    except Exception as e:
        return jsonify({
            "service": "Documents API", 
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Status endpoint"""
    return jsonify({
        "service": "Documents API",
        "status": "running",
        "version": "1.0.0"
    })

if __name__ == '__main__':
    log.info("API service starting...")
    log.info("Database connection test...")
    
    try:
        with db_manager.get_connection() as conn:
            log.info("Database connection successful")
    except Exception as e:
        log.error(f"Database connection failed: {e}")
    
    log.info("Starting Flask server on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=False)
