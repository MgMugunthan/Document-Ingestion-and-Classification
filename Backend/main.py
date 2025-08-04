import threading
import subprocess
from logger import log_agent_action
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
# Function to run a Python script in a thread with proper virtual environment
def run_script(script_path: str, label: str):
    print(f"{label} Starting...")
    log_agent_action(label.strip('🔁'), "-", "started", f"{label} started via main.py")
    
    # Map each component to its virtual environment Python executable
    component_python_map = {
        "Ingestor/Ingestor.py": "Ingestor/venv/Scripts/python.exe",
        "Ingestor/web_app.py": "Ingestor/venv/Scripts/python.exe", 
        "Extractor/Extractor.py": "Extractor/venv/Scripts/python.exe",
        "Classifier/Classifier.py": "Classifier/venv/Scripts/python.exe",
        "Router/Router.py": "Router/venv/Scripts/python.exe",
    }
    
    # Get the appropriate Python executable
    python_executable = component_python_map.get(script_path, "python")
    
    # If a python executable is found for the script, run it.
    if python_executable:
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


if __name__ == "__main__":
    threads = []

    # These are the services that will be started by the orchestrator
    agents = [
        ("Ingestor/Ingestor.py", " Ingestor"),
        ("Extractor/Extractor.py", " Extractor"),
        ("Classifier/Classifier.py", " Classifier"),
        ("Router/Router.py", " Router"),
        ("Ingestor/web_app.py", " Web App API"),
    ]

    for script, label in agents:
        t = threading.Thread(target=run_script, args=(script, label))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
