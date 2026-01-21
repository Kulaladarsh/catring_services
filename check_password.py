#!/usr/bin/env python3
"""
Script to check if a password matches a given hash.
"""

from werkzeug.security import check_password_hash

def check_password(password, hashed_password):
    """
    Check if the provided password matches the hashed password.
    """
    try:
        return check_password_hash(hashed_password, password)
    except Exception as e:
        print(f"Error checking password '{password}': {e}")
        return False

if __name__ == "__main__":
    # The hashed password from the user
    hashed = "scrypt:32768:8:1$KpGqF6ATMmKL70m9$3b9a772d0035f66f5ee5da773d4f17e3345c…"

    # Possible passwords to check
    possible_passwords = [
        "chetan@123%",
        "Chetan@23001867",
        "chetan@123",
        "Chetan@123%",
        "admin",
        "password"
    ]

    print("Checking possible passwords against the hash:")
    for pwd in possible_passwords:
        if check_password(pwd, hashed):
            print(f"✅ Password match found: '{pwd}'")
            break
    else:
        print("❌ No matching password found in the list.")
        print("The password might be different. You can add more passwords to the list.")
