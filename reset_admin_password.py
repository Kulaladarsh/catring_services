#!/usr/bin/env python3
"""
Script to reset admin password.
Run this from the project root directory.
"""

from backend.models import create_admin
from backend.db import admins_collection

def reset_admin_password():
    username = "Admin"
    new_password = "chetan@123%"

    # Check if admin exists
    existing = admins_collection.find_one({"username": username})
    if existing:
        print(f"Admin '{username}' already exists.")
        print("To reset the password, you need to delete the existing admin first.")
        print("Run this in Python shell to delete:")
        print(f"from backend.db import admins_collection")
        print(f"admins_collection.delete_one({{'username': '{username}'}})")
        print("Then run this script again.")
        return False

    # Create new admin
    result = create_admin(username, new_password)
    if result:
        print(f"✅ Admin '{username}' created with password '{new_password}'")
        return True
    else:
        print("❌ Failed to create admin")
        return False

if __name__ == "__main__":
    reset_admin_password()
