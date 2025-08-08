import threading
import subprocess
import logger
import os
import glob
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Kafka imports
from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

log = logger.get_agent_logger("main")

# Kafka configuration
KAFKA_TOPICS = ["doc.ingested", "doc.extracted", "doc.classified", "doc.routed"]

def wait_for_kafka(max_retries=30, delay=2):
    """Wait for Kafka to be available with retry mechanism."""
    import socket
    import time
    
    for attempt in range(max_retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 9092))
            sock.close()
            
            if result == 0:
                log.info(f"Kafka is available after {attempt + 1} attempts")
                return True
        except Exception as e:
            log.debug(f"Kafka connection attempt {attempt + 1} failed: {e}")
        
        if attempt < max_retries - 1:
            log.info(f"Waiting for Kafka... (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
    
    log.error(f"Kafka is not available after {max_retries} attempts")
    return False

def create_kafka_topics():
    """Create required Kafka topics if they don't exist."""
    if not wait_for_kafka():
        log.error("Kafka is not available - skipping topic creation")
        return False
    
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers='localhost:9092',
            client_id='admin'
        )
        
        topic_list = []
        for topic in KAFKA_TOPICS:
            topic_list.append(NewTopic(
                name=topic,
                num_partitions=1,
                replication_factor=1
            ))
        
        # Create topics and handle the response properly
        fs = admin_client.create_topics(new_topics=topic_list, validate_only=False)
        topic_created = 0
        topic_existing = 0
        
        # Handle the response - newer kafka-python versions return different objects
        if hasattr(fs, 'items'):
            # Older kafka-python API
            for topic, f in fs.items():
                try:
                    f.result()
                    log.info(f"Topic '{topic}' created successfully")
                    topic_created += 1
                except TopicAlreadyExistsError:
                    log.info(f"Topic '{topic}' already exists")
                    topic_existing += 1
                except Exception as e:
                    log.error(f"Failed to create topic '{topic}': {e}")
        else:
            # Newer kafka-python API - fs is a dict-like object with topic names as keys
            for topic in KAFKA_TOPICS:
                try:
                    if topic in fs:
                        fs[topic].result()  # This will raise an exception if creation failed
                        log.info(f"Topic '{topic}' created successfully")
                        topic_created += 1
                except TopicAlreadyExistsError:
                    log.info(f"Topic '{topic}' already exists")
                    topic_existing += 1
                except Exception as e:
                    log.error(f"Failed to create topic '{topic}': {e}")
        
        if topic_created > 0:
            log.info(f"Kafka setup complete: {topic_created} topics created, {topic_existing} already existed")
        else:
            log.info(f"Kafka setup complete: All {len(KAFKA_TOPICS)} topics already existed")
        return True
            
    except Exception as e:
        if "Connection" in str(e) or "timeout" in str(e).lower():
            log.warning(f"Kafka not available: {e}")
            log.info("System will continue without kafka setup")
        else:
            log.error(f"Kafka setup error: {e}")
        return False

# Function to run a Python script in a thread with the unified virtual environment
def run_script(script_path: str, label: str):
    log.info(f"{label} starting...")
    log.info(f"{label} started via main.py")
    
    # Use the single unified virtual environment for all components
    python_executable = "venv/Scripts/python.exe"
    
    # Run the script with the unified virtual environment
    subprocess.run([python_executable, script_path])

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
def status():
    return {"status": "Backend orchestrator is running"}

@app.get("/api/services/status")
def services_status():
    """Get status of all running services."""
    services = [
        {"name": "Auth Service", "port": 5001, "endpoint": "http://localhost:5001/api/health"},
        {"name": "Documents API", "port": 5002, "endpoint": "http://localhost:5002/api/health"},
        {"name": "Ingestor", "port": 5000, "endpoint": "http://localhost:5000/"},
        {"name": "Extractor", "port": None, "endpoint": None, "type": "background"},
        {"name": "Classifier", "port": None, "endpoint": None, "type": "background"},
        {"name": "Router", "port": None, "endpoint": None, "type": "background"},
    ]
    
    try:
        import requests
    except ImportError:
        # Fallback if requests is not available
        return {"services": [{"name": s["name"], "status": "unknown", "port": s.get("port")} for s in services]}
    
    status_list = []
    for service in services:
        service_status = {
            "name": service["name"],
            "port": service.get("port"),
            "status": "unknown",
            "type": service.get("type", "web_service")
        }
        
        if service.get("endpoint"):
            try:
                response = requests.get(service["endpoint"], timeout=3)
                if response.status_code == 200:
                    service_status["status"] = "running"
                    try:
                        data = response.json()
                        service_status["details"] = data
                    except:
                        pass
                else:
                    service_status["status"] = "error"
                    service_status["error"] = f"HTTP {response.status_code}"
            except requests.exceptions.ConnectionError:
                service_status["status"] = "down"
                service_status["error"] = "Connection refused"
            except requests.exceptions.Timeout:
                service_status["status"] = "timeout"
                service_status["error"] = "Request timeout"
            except Exception as e:
                service_status["status"] = "error"
                service_status["error"] = str(e)
        else:
            service_status["status"] = "background_service"
            
        status_list.append(service_status)
    
    return {
        "orchestrator": "running",
        "services": status_list,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }

@app.get("/api/kafka/topics")
def get_kafka_topics():
    """Get list of all Kafka topics."""
    return {"topics": KAFKA_TOPICS}

@app.get("/api/kafka/health")
def kafka_health():
    """Check Kafka health."""
    return {"status": "configured", "topics": KAFKA_TOPICS}

@app.get("/api/logs/stats")
def get_log_stats():
    """Get log directory statistics."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        return {"total_size_mb": 0, "file_count": 0, "files": []}
    
    log_files = glob.glob(os.path.join(log_dir, "*.log*"))
    total_size = 0
    files_info = []
    
    for file_path in log_files:
        try:
            size = os.path.getsize(file_path)
            files_info.append({
                "name": os.path.basename(file_path),
                "size_mb": round(size / (1024 * 1024), 2)
            })
            total_size += size
        except (OSError, IOError):
            continue
    
    files_info.sort(key=lambda x: x["size_mb"], reverse=True)
    
    return {
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_size_gb": round(total_size / (1024 * 1024 * 1024), 3),
        "file_count": len(files_info),
        "files": files_info,
        "warning": "Approaching 1GB limit" if total_size > 800 * 1024 * 1024 else None
    }

@app.post("/api/logs/clear")
def clear_logs():
    """Manually clear all log files."""
    try:
        result = logger.clear_all_logs()
        return {
            "success": True,
            "message": result["message"],
            "removed": result["removed"],
            "freed_mb": result["freed_mb"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/logs/auto-cleanup") 
def auto_cleanup_logs():
    """Auto-cleanup logs if over 1GB."""
    try:
        logger.check_and_cleanup_logs(max_total_size_gb=1.0)
        stats = get_log_stats()
        return {
            "success": True,
            "message": "Auto-cleanup completed",
            "current_stats": stats
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Initialize Kafka topics before starting services
    log.info("Initializing Kafka infrastructure...")
    create_kafka_topics()
    
    threads = []

    # These are the services that will be started by the orchestrator
    agents = [
        ("auth/auth.py", "Auth Service"),
        ("api/api.py", "Documents API"),
        ("ingestor/ingestor.py", "Ingestor"),
        ("extractor/extractor.py", "Extractor"),
        ("classifier/classifier.py", "Classifier"),
        ("router/router.py", "Router"),
    ]

    log.info("Starting all microservices...")
    for script, label in agents:
        t = threading.Thread(target=run_script, args=(script, label))
        t.daemon = True  # Make threads daemon so they exit when main exits
        t.start()
        threads.append(t)

    log.info("All services started. System is running...")
    for t in threads:
        t.join()
