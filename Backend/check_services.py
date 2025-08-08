#!/usr/bin/env python3
"""
Service Health Check Script
Tests all services started by main.py
"""

import requests
import json
from datetime import datetime

def check_service(name, url, timeout=3):
    """Check if a service is running and responsive."""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            try:
                data = response.json()
                return {"status": "✅ HEALTHY", "details": data}
            except json.JSONDecodeError:
                return {"status": "✅ RUNNING", "details": "HTML response"}
        else:
            return {"status": "⚠️ ERROR", "details": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "❌ DOWN", "details": "Connection refused"}
    except requests.exceptions.Timeout:
        return {"status": "⏱️ TIMEOUT", "details": "Request timed out"}
    except Exception as e:
        return {"status": "❌ ERROR", "details": str(e)}

def main():
    print("🔍 Document Management System - Service Health Check")
    print("=" * 60)
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    services = [
        ("Auth Service", "http://localhost:5001/api/health"),
        ("Ingestor Service", "http://localhost:5000/"),
        ("Ingestor API Status", "http://localhost:5000/api/status"),
    ]
    
    all_healthy = True
    
    for name, url in services:
        result = check_service(name, url)
        print(f"{name:<20} {result['status']}")
        
        if "details" in result and isinstance(result["details"], dict):
            # Pretty print JSON details
            for key, value in result["details"].items():
                if key in ['timestamp', 'status', 'service']:
                    print(f"{'':20}  {key}: {value}")
        elif "details" in result:
            print(f"{'':20}  {result['details']}")
        
        print()
        
        if "DOWN" in result['status'] or "ERROR" in result['status']:
            all_healthy = False
    
    print("=" * 60)
    if all_healthy:
        print("🎉 All services are running successfully!")
        print("✅ Your Document Management System is ready to use.")
        print()
        print("📱 Access points:")
        print("  • Frontend: http://localhost:3000")
        print("  • Auth API: http://localhost:5001")
        print("  • Main API: http://localhost:5000")
    else:
        print("⚠️ Some services are not responding properly.")
        print("💡 Make sure main.py is running: python main.py")
    
    print()

if __name__ == "__main__":
    main()
