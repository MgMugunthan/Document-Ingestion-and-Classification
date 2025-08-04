#!/usr/bin/env python3
"""
Simple Log Cleanup - One-liner commands for log management
Usage: python clear_logs.py [command]

Commands:
  stats    - Show log statistics
  clear    - Clear all logs
  auto     - Auto-cleanup if over 1GB
"""

import sys
import os
import logger

def show_stats():
    """Show log statistics."""
    import glob
    
    log_dir = "logs"
    if not os.path.exists(log_dir):
        print("❌ No logs directory found.")
        return
    
    log_files = glob.glob(os.path.join(log_dir, "*.log*"))
    if not log_files:
        print("📁 Logs directory is empty.")
        return
    
    total_size = sum(os.path.getsize(f) for f in log_files if os.path.exists(f))
    file_count = len(log_files)
    
    print(f"📊 Logs: {file_count} files, {total_size / (1024**2):.1f} MB ({total_size / (1024**3):.2f} GB)")
    
    if total_size > 1024**3:  # 1GB
        print("🚨 OVER 1GB LIMIT!")
    elif total_size > 800 * 1024**2:  # 800MB
        print("⚠️  Approaching 1GB limit")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        show_stats()
        return
    
    command = sys.argv[1].lower()
    
    if command == "stats":
        show_stats()
    
    elif command == "clear":
        confirm = input("⚠️  Delete ALL log files? (yes/no): ").strip().lower()
        if confirm in ['yes', 'y']:
            result = logger.clear_all_logs()
            print(f"✅ {result['message']}")
        else:
            print("❌ Cancelled.")
    
    elif command == "auto":
        print("🔍 Checking if cleanup needed...")
        logger.check_and_cleanup_logs(max_total_size_gb=1.0)
        show_stats()
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available: stats, clear, auto")

if __name__ == "__main__":
    main()
