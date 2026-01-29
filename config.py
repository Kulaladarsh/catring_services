import os
from datetime import timedelta

class Config:
    """
    Base configuration class for Flask application.
    Loads sensitive data from environment variables.
    """
    
    # Flask Settings
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=180)
    
    # MongoDB Settings
    MONGO_URI = os.getenv("MONGO_URI")
    
    # Email Settings (Flask-Mail)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@chetancatering.com")
    
    # WhatsApp Settings (Placeholder)
    WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "placeholder_key")
    WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "https://api.whatsapp.com/send")
    
    # Business Settings
    GST_PERCENTAGE = 5.0  # 5% GST
    SERVICE_CHARGE_PERCENTAGE = 10.0  # 10% service charge
    
    # Time Slots
    TIME_SLOTS = ["Morning", "Afternoon", "Night"]
    
    # Admin Settings
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCK_DURATION_MINUTES = 15
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "adarshkulal09@gmail.com")  # Default admin email

    # Base URL for PDF links
    BASE_URL = "https://chetan-catring-services.onrender.com"
