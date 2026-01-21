from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import timedelta

# Load environment variables
load_dotenv()

# =========================
# FLASK APP INITIALIZATION
# =========================

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Configuration
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
app.permanent_session_lifetime = timedelta(minutes=180)

# =========================
# MONGODB CONNECTION
# =========================

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    print("⚠️ WARNING: MONGO_URI not found in environment variables")
    mongo_uri = "mongodb://localhost:27017/catering_db"  # Fallback

app.config["MONGO_URI"] = mongo_uri

try:
    mongo = PyMongo(app)
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    mongo = None

# =========================
# REGISTER BLUEPRINTS
# =========================

# Frontend routes
from frontend_routes import frontend_bp
app.register_blueprint(frontend_bp)

# Admin routes (authentication & dashboard)
try:
    from backend.admin.routes import admin_bp
    app.register_blueprint(admin_bp)
    print("✅ Admin routes registered")
except ImportError as e:
    print(f"⚠️ Could not import admin routes: {e}")

# Admin API routes (dashboard data)
try:
    from backend.admin.api_routes import admin_api_bp
    app.register_blueprint(admin_api_bp)
    print("✅ Admin API routes registered at /admin/api")
except ImportError as e:
    print(f"⚠️ Could not import admin API routes: {e}")

# Public Dishes API (NO authentication required)
try:
    from backend.dishes.routes import dishes_bp
    app.register_blueprint(dishes_bp)
    print("✅ Public dishes API registered at /api/dishes")
except ImportError as e:
    print(f"⚠️ Could not import public dishes routes: {e}")

# Admin Dishes API (authentication required)
try:
    from backend.dishes.admin_routes import admin_dishes_bp
    app.register_blueprint(admin_dishes_bp)
    print("✅ Admin dishes API registered at /admin/api/dishes")
except ImportError as e:
    print(f"⚠️ Could not import admin dishes routes: {e}")

# Booking management routes
try:
    from backend.bookings.routes import bookings_bp
    app.register_blueprint(bookings_bp)
    print("✅ Bookings API registered")
except ImportError as e:
    print(f"⚠️ Could not import bookings routes: {e}")

# Ingredients/Grocery management routes
try:
    from backend.ingredients.routes import ingredients_bp
    app.register_blueprint(ingredients_bp)
    print("✅ Ingredients API registered at /admin/api/ingredients")
except ImportError as e:
    print(f"⚠️ Could not import ingredients routes: {e}")

# PDF generation and sending routes
try:
    from backend.utils.pdf_routes import pdf_bp
    app.register_blueprint(pdf_bp)
    print("✅ PDF API registered at /admin/api/pdf")
except ImportError as e:
    print(f"⚠️ Could not import PDF routes: {e}")

# =========================
# TEST ROUTES
# =========================

@app.route("/test")
def test():
    """Test MongoDB connection"""
    try:
        from backend.db import db
        if db:
            db.command('ping')
            return {"status": "success", "message": "✅ MongoDB Atlas Connected!"}
        else:
            return {"status": "error", "message": "❌ Database not initialized"}, 500
    except Exception as e:
        return {"status": "error", "message": f"❌ Connection failed: {e}"}, 500

@app.route("/hi")
def say_hi():
    return {
        "message": "Hi! Welcome to Catrings",
        "status": "Backend Active",
        "version": "2.0 - With Ingredients & PDF Features"
    }

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if mongo else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

# =========================
# ERROR HANDLERS
# =========================

@app.errorhandler(404)
def not_found(error):
    return {"error": "Resource not found"}, 404

@app.errorhandler(500)
def internal_error(error):
    return {"error": "Internal server error"}, 500

@app.errorhandler(400)
def bad_request(error):
    return {"error": "Bad request"}, 400

# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    from datetime import datetime

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
