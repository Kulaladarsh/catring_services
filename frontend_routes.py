
from flask import Blueprint, send_from_directory, render_template, request, redirect, url_for, session, flash

# ✅ This must match the import in app.py
frontend_bp = Blueprint("frontend_bp", __name__, template_folder="frontend")

# Home page
@frontend_bp.route("/")
def home():
    return send_from_directory("frontend", "landingpage.html")

# Services page - redirect to booking flow
@frontend_bp.route("/services")
def services():
    return redirect(url_for("frontend_bp.booking"))

# Menu page
@frontend_bp.route("/menu")
def menu():
    return send_from_directory("frontend", "dishselection.html")

# Booking flow
@frontend_bp.route("/booking")
def booking():
    return send_from_directory("frontend", "bookingflow.html")

# Order summary
@frontend_bp.route("/ordersummary")
def ordersummary():
    return send_from_directory("frontend", "ordersummary.html")

# Admin login page
@frontend_bp.route("/admin")
def admin_login():
    # If already logged in → go to dashboard
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.admin_dashboard"))

    return render_template("adminlogin.html")


# Dish selection page (alias for menu)
@frontend_bp.route("/dishes")
def dishes():
    return send_from_directory("frontend", "dishselection.html")

# Order summary page
@frontend_bp.route("/summary")
def summary():
    return send_from_directory("frontend", "ordersummary.html")

# Direct file routes for HTML navigation
@frontend_bp.route("/dishselection.html")
def dishselection_direct():
    return send_from_directory("frontend", "dishselection.html")

@frontend_bp.route("/ordersummary.html")
def ordersummary_direct():
    return send_from_directory("frontend", "ordersummary.html")

@frontend_bp.route("/menu.html")
def menu_direct():
    return send_from_directory("frontend", "dishselection.html")

@frontend_bp.route("/order_summary.html")
def order_summary_direct():
    return send_from_directory("frontend", "ordersummary.html")

# Index page (alias for home)
@frontend_bp.route("/index.html")
def index_direct():
    return send_from_directory("frontend", "landingpage.html")

# Services page (direct HTML)
@frontend_bp.route("/services.html")
def services_direct():
    return send_from_directory("frontend", "bookingflow.html")


