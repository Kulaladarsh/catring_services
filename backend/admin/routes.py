from flask import Blueprint, request, redirect, url_for, session, flash, render_template
from backend.models import validate_admin
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../../templates')

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET'])
def admin_login():
    """Admin login page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('adminlogin.html')


@admin_bp.route('/login', methods=['POST'])
def admin_login_post():
    """Handle admin login form submission"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Please provide both username and password', 'error')
        return redirect(url_for('admin.admin_login'))
    
    result = validate_admin(username, password)
    
    if result == True:
        session['admin_logged_in'] = True
        session['admin_username'] = username
        session.permanent = True
        flash('Login successful!', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    elif result == "LOCKED":
        flash('Account locked due to too many failed attempts. Please try again in 15 minutes.', 'error')
    else:
        flash('Invalid username or password', 'error')
    
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard page"""
    return render_template('admindashboard.html')


@admin_bp.route('/logout')
def admin_logout():
    """Logout admin user"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('admin.admin_login'))