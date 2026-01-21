from flask import Blueprint, request, jsonify, session
from backend.models import (
    check_slot_availability,
    create_booking,
    get_all_bookings,
    get_booking_by_id,
    update_booking_status,
    mark_ingredients_sent,
    log_admin_action
)
from backend.db import reserved_slots_collection
from backend.utils.email import (
    send_booking_confirmation,
    send_ingredients_list,
    send_admin_notification
)
from backend.utils.whatsapp import (
    send_booking_confirmation_whatsapp,
    send_ingredients_whatsapp
)
from datetime import datetime, timedelta
from functools import wraps
import re
from threading import Thread

bookings_bp = Blueprint("bookings", __name__, url_prefix="/api/bookings")

# =========================
# INPUT SANITIZATION
# =========================

def sanitize_string(text, max_length=500):
    """Remove potentially harmful characters from string input"""
    if not text or not isinstance(text, str):
        return ""
    # Remove HTML tags and script content
    text = re.sub(r'<[^>]*?>', '', text)
    # Remove script tags content
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    # Limit length
    return text[:max_length].strip()

def sanitize_email(email):
    """Validate and sanitize email"""
    if not email:
        return ""
    email = email.strip().lower()
    # Basic email validation
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return ""
    return email[:254]  # Max email length

def sanitize_mobile(mobile):
    """Validate and sanitize mobile number"""
    if not mobile:
        return ""
    # Remove all non-digit characters except +
    mobile = re.sub(r'[^\d+]', '', mobile)
    # Ensure it starts with +91
    if not mobile.startswith('+91'):
        mobile = '+91' + mobile.lstrip('+')
    # Validate length
    if len(mobile) != 13:  # +91 + 10 digits
        return ""
    return mobile

def validate_date(date_str):
    """Validate date format and ensure it's not in the past"""
    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d")
        if event_date.date() < datetime.now().date():
            return None, "Cannot book past dates"
        return event_date, None
    except ValueError:
        return None, "Invalid date format. Use YYYY-MM-DD"

# =========================
# ASYNC NOTIFICATION HELPER
# =========================

def send_notifications_async(booking, customer_data):
    """Send notifications in background thread to avoid blocking"""
    def _send():
        try:
            # Email confirmation
            send_booking_confirmation(
                customer_email=customer_data["email"],
                customer_name=customer_data["name"],
                booking_details=booking
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        try:
            # WhatsApp confirmation
            send_booking_confirmation_whatsapp(
                phone_number=customer_data["mobile"],
                customer_name=customer_data["name"],
                booking_details=booking
            )
        except Exception as e:
            print(f"WhatsApp sending failed: {e}")
        
        try:
            # Admin notification
            send_admin_notification(booking)
        except Exception as e:
            print(f"Admin notification failed: {e}")
    
    # Start background thread
    thread = Thread(target=_send)
    thread.daemon = True
    thread.start()

# =========================
# DECORATOR: ADMIN REQUIRED
# =========================

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return wrapper

# =========================
# CHECK SLOT AVAILABILITY
# =========================

@bookings_bp.route("/check-availability", methods=["POST"])
def check_availability():
    """
    Public API: Checks if a time slot is available for booking.
    """
    data = request.get_json()
    
    date = sanitize_string(data.get("date", ""), 10)
    time_slot = sanitize_string(data.get("time_slot", ""), 20)
    
    if not date or not time_slot:
        return jsonify({"error": "Date and time_slot are required"}), 400
    
    # Validate date
    event_date, error = validate_date(date)
    if error:
        return jsonify({"available": False, "message": error}), 400
    
    # Validate time slot
    if time_slot not in ["Morning", "Afternoon", "Night"]:
        return jsonify({"error": "Invalid time slot"}), 400
    
    # Check availability
    available = check_slot_availability(date, time_slot)
    
    return jsonify({
        "available": available,
        "date": date,
        "time_slot": time_slot,
        "message": "Slot is available" if available else "Slot already booked"
    })

# =========================
# GET AVAILABLE SLOTS FOR DATE
# =========================

@bookings_bp.route("/available-slots/<date>", methods=["GET"])
def get_available_slots(date):
    """
    Public API: Returns available time slots for a specific date.
    """
    date = sanitize_string(date, 10)
    
    # Validate date
    event_date, error = validate_date(date)
    if error:
        return jsonify({
            "error": error,
            "available_slots": [],
            "booked_slots": []
        }), 400
    
    all_slots = ["Morning", "Afternoon", "Night"]
    available_slots = []
    booked_slots = []
    
    for slot in all_slots:
        if check_slot_availability(date, slot):
            available_slots.append(slot)
        else:
            booked_slots.append(slot)
    
    return jsonify({
        "date": date,
        "available_slots": available_slots,
        "booked_slots": booked_slots,
        "is_fully_booked": len(available_slots) == 0
    })

# =========================
# GET BOOKED DATES OVERVIEW
# =========================

@bookings_bp.route("/booked-dates", methods=["GET"])
def get_booked_dates():
    """
    Public API: Returns overview of all dates with booking status.
    """
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$date",
                    "booked_slots": {"$addToSet": "$time_slot"},
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]

        booked_dates_result = list(reserved_slots_collection.aggregate(pipeline))

        fully_booked_dates = []
        partially_booked_dates = []
        all_slots = ["Morning", "Afternoon", "Night"]
        today = datetime.now().date()

        for result in booked_dates_result:
            date = result["_id"]
            booked_slots = result["booked_slots"]

            # Skip past dates
            try:
                event_date = datetime.strptime(date, "%Y-%m-%d").date()
                if event_date < today:
                    continue
            except:
                continue

            # Check if all 3 slots are booked
            if len(booked_slots) >= 3:
                fully_booked_dates.append(date)
            else:
                available_slots = [s for s in all_slots if s not in booked_slots]
                partially_booked_dates.append({
                    "date": date,
                    "booked_slots": booked_slots,
                    "available_slots": available_slots
                })

        return jsonify({
            "success": True,
            "fully_booked_dates": fully_booked_dates,
            "partially_booked_dates": partially_booked_dates
        })

    except Exception as e:
        return jsonify({"error": f"Failed to fetch booked dates: {str(e)}"}), 500

# =========================
# CREATE BOOKING (OPTIMIZED)
# =========================

@bookings_bp.route("/", methods=["POST"])
def create_new_booking():
    """
    Public API: Creates a new booking with validation and sanitization.
    Optimized for fast response with async notifications.
    """
    data = request.get_json()
    
    # Sanitize and validate inputs
    customer_name = sanitize_string(data.get("customer_name", ""), 100)
    mobile = sanitize_mobile(data.get("mobile", ""))
    email = sanitize_email(data.get("email", ""))
    event_location = sanitize_string(data.get("event_location", ""), 500)
    map_link = sanitize_string(data.get("map_link", ""), 500)
    service_type = sanitize_string(data.get("service_type", "Catering Service"), 100)
    event_date = sanitize_string(data.get("event_date", ""), 10)
    time_slot = sanitize_string(data.get("time_slot", ""), 20)
    food_preference = sanitize_string(data.get("food_preference", ""), 50)
    
    # Validate required fields
    if not customer_name or len(customer_name) < 2:
        return jsonify({"error": "Valid customer name is required"}), 400
    
    if not mobile:
        return jsonify({"error": "Valid mobile number is required"}), 400
    
    if not email:
        return jsonify({"error": "Valid email is required"}), 400
    
    if not event_location:
        return jsonify({"error": "Event location is required"}), 400
    
    # Validate date
    event_date_obj, error = validate_date(event_date)
    if error:
        return jsonify({"error": error}), 400
    
    # Validate time slot
    valid_slots = ["Morning", "Afternoon", "Night"]
    if time_slot not in valid_slots:
        return jsonify({"error": f"Invalid time slot"}), 400
    
    # Validate guests
    try:
        guests = int(data.get("guests", 0))
        if guests < 1 or guests > 10000:
            return jsonify({"error": "Invalid number of guests"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid number of guests"}), 400
    
    # Validate dishes
    selected_dishes = data.get("selected_dishes", [])
    if not selected_dishes or not isinstance(selected_dishes, list) or len(selected_dishes) == 0:
        return jsonify({"error": "At least one dish must be selected"}), 400
    
    # Sanitize dishes
    sanitized_dishes = []
    for dish in selected_dishes:
        if not isinstance(dish, dict):
            continue
        dish_id = sanitize_string(str(dish.get("dish_id", "")), 50)
        try:
            quantity = int(dish.get("quantity", 0))
            if quantity > 0 and quantity <= 10000:
                sanitized_dishes.append({
                    "dish_id": dish_id,
                    "quantity": quantity
                })
        except (ValueError, TypeError):
            continue
    
    if not sanitized_dishes:
        return jsonify({"error": "No valid dishes selected"}), 400
    
    # CRITICAL: Check availability immediately before creating booking
    if not check_slot_availability(event_date, time_slot):
        return jsonify({
            "error": "This time slot is no longer available",
            "message": "The slot was booked by another user. Please select a different date or time slot.",
            "code": "SLOT_UNAVAILABLE"
        }), 409
    
    # Prepare sanitized booking data
    booking_data = {
        "customer_name": customer_name,
        "mobile": mobile,
        "email": email,
        "event_location": event_location,
        "map_link": map_link,
        "service_type": service_type,
        "event_date": event_date,
        "time_slot": time_slot,
        "guests": guests,
        "food_preference": food_preference,
        "selected_dishes": sanitized_dishes
    }
    
    # Create booking
    try:
        booking_id = create_booking(booking_data)
        
        if not booking_id:
            return jsonify({
                "error": "Booking failed",
                "message": "Slot may have been booked by another user. Please try again.",
                "code": "BOOKING_FAILED"
            }), 409
        
        # Get complete booking details
        booking = get_booking_by_id(booking_id)
        
        # Send notifications asynchronously (non-blocking)
        send_notifications_async(booking, {
            "email": email,
            "mobile": mobile,
            "name": customer_name
        })
        
        # Return success immediately
        return jsonify({
            "success": True,
            "message": "Booking created successfully",
            "booking_id": booking_id,
            "booking": booking
        }), 201
        
    except Exception as e:
        print(f"Booking creation error: {e}")
        return jsonify({"error": "Booking creation failed. Please try again."}), 500

# =========================
# GET ALL BOOKINGS (ADMIN)
# =========================

@bookings_bp.route("/", methods=["GET"])
@admin_required
def get_bookings():
    """
    Admin API: Returns all bookings with optional filters.
    """
    filters = {}
    
    # Build filter query with sanitization
    if request.args.get("date"):
        filters["event_date"] = sanitize_string(request.args.get("date"), 10)
    
    if request.args.get("time_slot"):
        filters["time_slot"] = sanitize_string(request.args.get("time_slot"), 20)
    
    if request.args.get("status"):
        filters["status"] = sanitize_string(request.args.get("status"), 20)
    
    if request.args.get("service_type"):
        filters["service_type"] = sanitize_string(request.args.get("service_type"), 100)
    
    bookings = get_all_bookings(filters if filters else None)
    
    return jsonify({
        "success": True,
        "bookings": bookings,
        "count": len(bookings)
    })

# =========================
# GET SINGLE BOOKING
# =========================

@bookings_bp.route("/<booking_id>", methods=["GET"])
@admin_required
def get_booking(booking_id):
    """
    Admin API: Returns details of a single booking.
    """
    booking_id = sanitize_string(booking_id, 50)
    booking = get_booking_by_id(booking_id)
    
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    return jsonify({
        "success": True,
        "booking": booking
    })

# =========================
# UPDATE BOOKING STATUS
# =========================

@bookings_bp.route("/<booking_id>/status", methods=["PATCH"])
@admin_required
def update_status(booking_id):
    """
    Admin API: Updates booking status.
    """
    booking_id = sanitize_string(booking_id, 50)
    data = request.get_json()
    status = sanitize_string(data.get("status", ""), 20)
    
    valid_statuses = ["Pending", "Confirmed", "Completed", "Cancelled"]
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status"}), 400
    
    # Check if booking exists
    booking = get_booking_by_id(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    success = update_booking_status(booking_id, status)
    
    if success:
        username = session.get("admin_username", "unknown")
        log_admin_action(username, f"BOOKING_STATUS_UPDATED: {booking_id} -> {status}")
        
        return jsonify({
            "success": True,
            "message": f"Booking status updated to {status}"
        })
    else:
        return jsonify({"error": "Status update failed"}), 500

# =========================
# SEND INGREDIENTS LIST
# =========================

@bookings_bp.route("/<booking_id>/send-ingredients", methods=["POST"])
@admin_required
def send_ingredients(booking_id):
    """
    Admin API: Sends ingredients list to customer.
    """
    booking_id = sanitize_string(booking_id, 50)
    data = request.get_json()
    ingredients = sanitize_string(data.get("ingredients", ""), 5000)
    
    if not ingredients:
        return jsonify({"error": "Ingredients list is required"}), 400
    
    # Get booking details
    booking = get_booking_by_id(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    try:
        # Send via email
        email_sent = send_ingredients_list(
            customer_email=booking["email"],
            customer_name=booking["customer_name"],
            booking_details=booking,
            ingredients_list=ingredients
        )
        
        # Send via WhatsApp
        whatsapp_sent = send_ingredients_whatsapp(
            phone_number=booking["mobile"],
            customer_name=booking["customer_name"],
            booking_details=booking,
            ingredients_list=ingredients
        )
        
        # Mark as sent
        mark_ingredients_sent(booking_id)
        
        # Log action
        username = session.get("admin_username", "unknown")
        log_admin_action(username, f"INGREDIENTS_SENT: {booking_id}")
        
        return jsonify({
            "success": True,
            "message": "Ingredients list sent successfully",
            "email_sent": email_sent,
            "whatsapp_sent": whatsapp_sent
        })
        
    except Exception as e:
        print(f"Ingredients sending error: {e}")
        return jsonify({"error": "Failed to send ingredients"}), 500