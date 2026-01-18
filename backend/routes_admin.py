from flask import Blueprint, request, redirect, url_for, session, flash, render_template
from backend.models import validate_admin
from functools import wraps

admin_bp = Blueprint("admin", __name__, template_folder="../frontend")

# ---------------- LOGIN REQUIRED ----------------
def admin_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("frontend.admin_login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------- LOGIN POST ----------------
@admin_bp.route("/admin/login", methods=["POST"])
def admin_login_post():
    username = request.form.get("username")
    password = request.form.get("password")

    result = validate_admin(username, password)

    if result is True:
        session["admin_logged_in"] = True
        session["admin_username"] = username
        return redirect(url_for("admin.admin_dashboard"))

    elif result == "LOCKED":
        flash("Account locked. Try again later.", "danger")
    else:
        flash("Invalid username or password", "danger")

    return redirect(url_for("frontend.admin_login"))


# ---------------- DASHBOARD ----------------
@admin_bp.route("/admin/dashboard")
@admin_login_required
def admin_dashboard():
    return render_template("admindashboard.html")


# ---------------- LOGOUT ----------------
@admin_bp.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("frontend.admin_login"))
