import logging
import os
import sys
import io
import json
from datetime import datetime
from colorama import Fore, Style, init
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

init(autoreset=True)  # Reset color after each print

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "agent.log")

class ColorFormatter(logging.Formatter):
    def format(self, record):
        level_color = {
            "INFO": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "DEBUG": Fore.BLUE,
        }.get(record.levelname, "")
        return f"{level_color}{record.levelname:<8} - {record.msg}{Style.RESET_ALL}"
def log_event(agent, message):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{agent}] {message}")
    

import logging
import sys

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding handlers multiple times
    if logger.hasHandlers():
        return logger

    # Console handler with UTF-8 encoding to avoid emoji crashes
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)

    # Safely handle emoji in console (force UTF-8)
    stream_handler.setFormatter(logging.Formatter('%(levelname)-8s - %(message)s'))
    try:
        stream_handler.stream.reconfigure(encoding='utf-8')  # Python 3.7+
    except Exception:
        pass

    logger.addHandler(stream_handler)

    return logger

def log_agent_action(agent: str, doc_id: str, status: str, message: str, filename: str = None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{agent.upper()}] [{status.upper()}] Doc ID: {doc_id} - {message}\n"

    # Write to common agent.log
    agent_log_path = os.path.join(LOG_DIR, "agent.log")
    with open(agent_log_path, "a", encoding="utf-8") as f:
        f.write(log_line)

    # If filename is provided, log separately too
    if filename:
        filename_log_path = os.path.join(LOG_DIR, f"{filename}.log")
        with open(filename_log_path, "a", encoding="utf-8") as f:
            f.write(log_line)

