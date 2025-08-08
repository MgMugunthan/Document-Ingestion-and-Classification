"""
Document Ingestor Service - Main Entry Point

A modular ingestor that handles file uploads, Gmail integration,
and document processing pipeline coordination.

Architecture:
- ingestor_core.py: Core document processing logic
- gmail_handler.py: Gmail integration functionality  
- flask_routes.py: Web API routes
- ingestor.py: Main orchestrator (this file)
"""

import os
import sys
from flask import Flask
from flask_cors import CORS

# Add parent directory for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

# Import our modules
from ingestor_core import IngestorCore
from gmail_handler import GmailHandler
from flask_routes import create_routes

class DocumentIngestor:
    """Main document ingestor orchestrator."""
    
    def __init__(self):
        self.log = logger.get_agent_logger("Ingestor")
        
        # Initialize core components
        self.core = IngestorCore()
        self.gmail_handler = GmailHandler(
            config=self.core.config,
            db_manager=self.core.db,
            emit_callback=self.core.emit_to_kafka
        )
        
        # Setup Flask app
        self.flask_app = self._setup_flask()
        
    def _setup_flask(self):
        """Initialize Flask app with routes."""
        app = Flask(__name__)
        CORS(app)
        
        # Register routes
        routes_bp = create_routes(self.core, self.gmail_handler)
        app.register_blueprint(routes_bp)
        
        return app
    
    def start_services(self):
        """Start all ingestor services."""
        self.log.info(" Starting Document Ingestor Service...")
        
        try:
            # Start file watcher
            self.core.start_file_watcher()
            
            # Start Gmail monitor if available
            self.gmail_handler.start_monitor()
            
            # Start Flask web server
            self.log.info(f" Starting web server on port {self.core.config.web_port}...")
            self.log.info(" Document Ingestor Service ready!")
            self.log.info(f" Monitoring folder: {self.core.config.files_dir}")
            self.log.info(f" Web interface: http://localhost:{self.core.config.web_port}")
            self.log.info(f" Gmail integration: {' Enabled' if self.gmail_handler.is_available() else ' Disabled'}")
            
            self.flask_app.run(
                host='0.0.0.0', 
                port=self.core.config.web_port, 
                debug=False,
                threaded=True
            )
            
        except KeyboardInterrupt:
            self.log.info("  Ingestor service stopped by user.")
        except Exception as e:
            self.log.error(f" Ingestor service failed: {e}")
        finally:
            self.core.stop_services()
            self.log.info(" Document Ingestor Service shutdown complete.")

def main():
    """Main entry point."""
    ingestor = DocumentIngestor()
    ingestor.start_services()

if __name__ == "__main__":
    main()
