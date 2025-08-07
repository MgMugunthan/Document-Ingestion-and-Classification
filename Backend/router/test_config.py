#!/usr/bin/env python3
"""
Test script for the router configuration
"""

import os
import sys
import json

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the router functions
from router import load_routes_config, get_routing_stats

def test_router_config():
    """Test the router configuration loading."""
    print("=== Testing Router Configuration ===\n")
    
    # Test loading configuration
    config = load_routes_config()
    print("1. Configuration loaded:")
    print(json.dumps(config, indent=2))
    print()
    
    # Test routing stats
    stats = get_routing_stats()
    print("2. Routing statistics:")
    for key, value in stats.items():
        if isinstance(value, set):
            print(f"   {key}: {list(value)}")
        else:
            print(f"   {key}: {value}")
    print()
    
    # Test document type mappings
    test_documents = [
        ("resume", 0.8),
        ("cv", 0.9),
        ("receipt", 0.75),
        ("invoice", 0.85),
        ("bill", 0.7),
        ("contract", 0.8),  # Should go to default
        ("report", 0.9),    # Should go to default
        ("resume", 0.6),    # Low confidence - should go to needs_action
        ("unknown", 0.3)    # Low confidence - should go to needs_action
    ]
    
    print("3. Test document routing decisions:")
    for doc_type, confidence in test_documents:
        if confidence < config["confidence_threshold"]:
            target = config["needs_action_folder"]
            reason = f"Low confidence ({confidence:.1f})"
        elif doc_type.lower() in config["routes"]:
            target = config["routes"][doc_type.lower()]
            reason = f"Mapped route ({confidence:.1f})"
        else:
            target = config["default_folder"]
            reason = f"Default route ({confidence:.1f})"
        
        print(f"   {doc_type} ({confidence:.1f}) → {target} ({reason})")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_router_config()
