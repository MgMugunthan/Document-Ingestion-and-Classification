import threading
import subprocess
from logger import log_agent_action
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# Function to run a Python script in a thread
def run_script(script_path: str, label: str):
    print(f"{label} 🚀 starting...")
    log_agent_action(label.strip('🔁'), "-", "started", f"{label} started via main.py")
    subprocess.run(["python", script_path])

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
    return {"status": "Backend is running"}

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    # Save or process the file here
    return {"filename": file.filename}

if __name__ == "__main__":
    threads = []

    agents = [
        ("ingestor/ingestor.py", "📥 Ingestor"),
        ("Extractor/extractor.py", "📄 Extractor"),
        ("Classifier/classifier.py", "🧠 Classifier"),
        ("Router/router.py", "📁 Router"),
        ("logger.py", "logger 🔁"),
        ("ingestor/web_app.py", "🌐 Web App"),
    ]

    for script, label in agents:
        t = threading.Thread(target=run_script, args=(script, label))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
