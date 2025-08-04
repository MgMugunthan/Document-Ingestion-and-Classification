import logging
import os
import sys
import glob
from logging.handlers import RotatingFileHandler
from colorama import Fore, Style, init

# Initialize colorama to add color to console output and reset automatically
init(autoreset=True)

class ColorFormatter(logging.Formatter):
    """A custom formatter to add colors to log levels for console output."""
    def format(self, record):
        level_color = {
            "INFO": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "DEBUG": Fore.BLUE,
        }.get(record.levelname, "")
        # Format the message with color and reset style at the end
        return f"{level_color}{record.levelname:<8}{Style.RESET_ALL} - {record.msg}"

def check_and_cleanup_logs(log_dir="logs", max_total_size_gb=1.0):
    """
    Check total log directory size and cleanup if it exceeds the limit.
    
    Args:
        log_dir (str): Directory containing log files
        max_total_size_gb (float): Maximum total size in GB before cleanup
    """
    if not os.path.exists(log_dir):
        return
    
    # Get all log files
    log_files = glob.glob(os.path.join(log_dir, "*.log*"))
    
    # Calculate total size
    total_size = 0
    file_info = []
    
    for file_path in log_files:
        try:
            size = os.path.getsize(file_path)
            modified_time = os.path.getmtime(file_path)
            file_info.append((file_path, size, modified_time))
            total_size += size
        except (OSError, IOError):
            continue
    
    # Check if cleanup is needed
    max_size_bytes = max_total_size_gb * 1024 * 1024 * 1024  # Convert GB to bytes
    
    if total_size > max_size_bytes:
        print(f"\n⚠️  Log directory ({total_size / (1024**3):.2f} GB) exceeds {max_total_size_gb} GB limit.")
        print("🧹 Auto-cleaning oldest log files...")
        
        # Sort files by modification time (oldest first)
        file_info.sort(key=lambda x: x[2])
        
        # Remove oldest files until we're under the limit
        removed_count = 0
        freed_size = 0
        
        for file_path, size, _ in file_info:
            if total_size <= max_size_bytes * 0.8:  # Stop when we're at 80% of limit
                break
            
            # Don't remove current log files (those without number suffix)
            if file_path.endswith('.log') and not any(file_path.endswith(f'.log.{i}') for i in range(1, 10)):
                continue
            
            try:
                os.remove(file_path)
                total_size -= size
                freed_size += size
                removed_count += 1
                print(f"   Removed: {os.path.basename(file_path)} ({size / (1024**2):.1f} MB)")
            except (OSError, IOError) as e:
                print(f"   Error removing {file_path}: {e}")
        
        if removed_count > 0:
            print(f"✅ Cleanup complete: Removed {removed_count} files, freed {freed_size / (1024**2):.1f} MB")
            print(f"📊 New total size: {total_size / (1024**3):.2f} GB")
        else:
            print("⚠️  No old files to remove. Consider manual cleanup of current log files.")

def clear_all_logs(log_dir="logs"):
    """
    Manually clear all log files in the directory.
    
    Args:
        log_dir (str): Directory containing log files
    
    Returns:
        dict: Summary of cleanup operation
    """
    if not os.path.exists(log_dir):
        return {"removed": 0, "freed_mb": 0, "message": "Log directory does not exist"}
    
    log_files = glob.glob(os.path.join(log_dir, "*.log*"))
    
    removed_count = 0
    freed_size = 0
    errors = []
    
    for file_path in log_files:
        try:
            size = os.path.getsize(file_path)
            os.remove(file_path)
            removed_count += 1
            freed_size += size
        except (OSError, IOError) as e:
            errors.append(f"{os.path.basename(file_path)}: {e}")
    
    result = {
        "removed": removed_count,
        "freed_mb": round(freed_size / (1024 * 1024), 2),
        "message": f"Cleared {removed_count} log files, freed {freed_size / (1024**2):.1f} MB"
    }
    
    if errors:
        result["errors"] = errors
    
    return result

def get_agent_logger(agent_name: str):
    """
    Configures and returns a logger for a specific agent with smart space management.

    This function creates a logger that writes to two places:
    1. A rotating log file for the agent (e.g., 'logs/router.log').
       - Auto-rotates at 50MB per file to prevent huge single files
       - Keeps 3 backup files per service (total ~200MB per service max)
    2. The console, with colored output for different log levels.

    Features:
    - Automatic cleanup when total logs exceed 1GB
    - Manual cleanup function available
    - Rotating files to prevent single huge files
    """
    # Ensure the agent name is lowercase for consistency in filenames
    agent_name = agent_name.lower()
    
    # Create a 'logs' directory in the current working directory of the script
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"{agent_name}.log")

    # Check and cleanup logs if they're getting too large
    check_and_cleanup_logs(log_dir, max_total_size_gb=1.0)

    # Get the logger instance for the agent
    logger = logging.getLogger(agent_name)
    logger.setLevel(logging.INFO)

    # Prevent adding duplicate handlers if the logger is requested multiple times
    if logger.hasHandlers():
        return logger

    # --- Rotating File Handler ---
    # This handler writes log messages with automatic rotation
    # maxBytes=50MB, backupCount=3 means:
    # - agent.log (current, up to 50MB)
    # - agent.log.1, agent.log.2, agent.log.3 (older rotations)
    # Total per service: ~200MB maximum
    file_handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=50*1024*1024,  # 50MB per file
        backupCount=3,          # Keep 3 backup files
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
        '%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # --- Console (Stream) Handler ---
    # This handler prints log messages to the console (e.g., your terminal).
    stream_handler = logging.StreamHandler(sys.stdout)
    # Use our custom ColorFormatter for pretty, colored output
    stream_handler.setFormatter(ColorFormatter())
    logger.addHandler(stream_handler)

    return logger


