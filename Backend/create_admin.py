#!/usr/bin/env python3
"""
Admin User Creation Utility

Creates an admin user in the document management system.
Run this script to create your first admin user after removing the default admin.
"""

import sys
import os
from werkzeug.security import generate_password_hash
from getpass import getpass

# Add parent directory for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import db_manager

def create_admin_user():
    """Create a new admin user interactively."""
    
    print("🔐 Admin User Creation Utility")
    print("=" * 40)
    
    # Get user input
    user_id = input("Enter admin username: ").strip()
    if not user_id:
        print("❌ Username cannot be empty!")
        return False
    
    email = input("Enter admin email: ").strip()
    if not email:
        print("❌ Email cannot be empty!")
        return False
    
    password = getpass("Enter admin password: ").strip()
    if not password:
        print("❌ Password cannot be empty!")
        return False
    
    password_confirm = getpass("Confirm admin password: ").strip()
    if password != password_confirm:
        print("❌ Passwords do not match!")
        return False
    
    department = input("Enter department (default: IT): ").strip() or "IT"
    
    try:
        # Check if user already exists
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                print(f"❌ User '{user_id}' already exists!")
                return False
            
            # Create the admin user
            password_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (user_id, email, password_hash, user_type, department)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, email, password_hash, 'admin', department))
            conn.commit()
            
            print(f"✅ Admin user '{user_id}' created successfully!")
            print(f"📧 Email: {email}")
            print(f"🏢 Department: {department}")
            print(f"👤 User Type: admin")
            print("\n🚀 You can now log in to the system with these credentials.")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def list_existing_users():
    """List existing users in the system."""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, email, user_type, department FROM users ORDER BY user_type DESC, user_id")
            users = cursor.fetchall()
            
            if users:
                print("\n👥 Existing Users:")
                print("-" * 60)
                print(f"{'Username':<15} {'Email':<25} {'Type':<10} {'Department'}")
                print("-" * 60)
                for user in users:
                    user_id, email, user_type, dept = user
                    print(f"{user_id:<15} {email:<25} {user_type:<10} {dept}")
            else:
                print("\n📝 No users found in the system.")
                
    except Exception as e:
        print(f"❌ Error listing users: {e}")

if __name__ == "__main__":
    print("Document Management System - Admin Setup")
    print("========================================\n")
    
    while True:
        print("1. Create new admin user")
        print("2. List existing users") 
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            print()
            if create_admin_user():
                print("\n✨ Admin creation completed!")
                break
            else:
                print("\n⚠️  Admin creation failed. Try again.")
                
        elif choice == "2":
            list_existing_users()
            
        elif choice == "3":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1, 2, or 3.")
        
        print()
