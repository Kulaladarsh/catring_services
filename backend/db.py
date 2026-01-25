from pymongo import MongoClient
from dotenv import load_dotenv
import os
import urllib.parse

# Load environment variables
load_dotenv()

def get_mongo_uri():
    """
    Safely constructs MongoDB URI with encoded password.
    Handles special characters in passwords.
    """
    MONGO_URI = os.getenv("MONGO_URI")
    
    if not MONGO_URI:
        raise ValueError("MONGO_URI not found in environment variables")
    
    # Parse and encode password if it contains special characters
    if MONGO_URI.startswith("mongodb+srv://"):
        parts = MONGO_URI.replace("mongodb+srv://", "").split("@")
        if len(parts) == 2:
            user_pass = parts[0].split(":")
            if len(user_pass) == 2:
                username, password = user_pass
                encoded_password = urllib.parse.quote(password, safe='')
                cluster_db = parts[1]
                return f"mongodb+srv://{username}:{encoded_password}@{cluster_db}"
    
    return MONGO_URI

# Initialize MongoDB connection
try:
    MONGO_URI = get_mongo_uri()
    client = MongoClient(MONGO_URI)
    db = client["catering_db"]
    
    # Test connection
    client.server_info()
    print("✅ MongoDB Atlas connected successfully")
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    db = None

# =========================
# COLLECTION REFERENCES
# =========================

# Admin Collections
admins_collection = db["admins"] if db is not None else None
admin_logs_collection = db["admin_logs"] if db is not None else None

# Dish Collections
dishes_collection = db["dishes"] if db is not None else None

# Categories Collection
categories_collection = db["categories"] if db is not None else None

# Order Collections
orders_collection = db["orders"] if db is not None else None
reserved_slots_collection = db["reserved_slots"] if db is not None else None

# Grocery/Ingredients Collections
ingredients_collection = db["ingredients"] if db is not None else None
final_ingredients_collection = db["final_ingredients"] if db is not None else None  # ADDED THIS

# Notification Collections
notifications_collection = db["notifications"] if db is not None else None

# User Ratings Collection
user_ratings_collection = db["user_ratings"] if db is not None else None

# New Automatic Ratings Collection (linked to bookings)
ratings_collection = db["ratings"] if db is not None else None
