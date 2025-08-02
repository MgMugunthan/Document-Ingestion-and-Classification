import threading
import subprocess
from logger import log_agent_action

# Function to run a Python script in a thread
def run_script(script_path: str, label: str):
    print(f"{label} 🚀 starting...")
    log_agent_action(label.strip('🔁'), "-", "started", f"{label} started via main.py")
    subprocess.run(["python", script_path])

if __name__ == "__main__":
    threads = []

    agents = [
        ("ingestor/ingestor.py", "📥 Ingestor"),
        ("Extractor/extractor.py", "📄 Extractor"),
        ("Classifier/classifier.py", "🧠 Classifier"),
        ("Router/router.py", "📁 Router"),
        ("logger.py", "logger 🔁"),
    ]

    for script, label in agents:
        t = threading.Thread(target=run_script, args=(script, label))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
