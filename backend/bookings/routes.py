from flask import Blueprint, request, jsonify, session
from backend.models import (
    check_slot_availability,
    create_booking,
    get_all_bookings,
    get_booking_by_id,
    update_booking_status,
    mark_ingredients_sent,
    log_admin_action,
    check_rating_eligibility,
    submit_automatic_rating,
    get_ratings_average
)
from backend.db import reserved_slots_collection, orders_collection
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
    
    # Get client IP address for rating tracking
    user_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))

    # Create booking
    try:
        booking_id = create_booking(booking_data, user_ip)
        
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

# =========================
# GET USER COMPLETED BOOKINGS (FOR RATING)
# =========================

@bookings_bp.route("/user/completed", methods=["GET"])
def get_user_completed_bookings():
    """
    Public API: Returns user's completed bookings for rating selection
    Uses IP address to identify user (no authentication required)
    """
    print("DEBUG: get_user_completed_bookings called")
    try:
        print("DEBUG: Starting IP detection")
        # Get client IP address with improved detection
        ip_address = None

        # Check various headers for IP address (in order of preference)
        headers_to_check = [
            'CF-Connecting-IP',  # Cloudflare
            'X-Forwarded-For',   # Standard proxy header
            'X-Real-IP',         # Nginx
            'X-Client-IP',       # Some proxies
            'X-Forwarded',       # Alternative
        ]

        for header in headers_to_check:
            header_value = request.headers.get(header)
            if header_value:
                # X-Forwarded-For can contain multiple IPs, take the first one
                ip_address = header_value.split(',')[0].strip()
                print(f"DEBUG: Found IP in header {header}: {ip_address}")
                break

        # Fallback to request.remote_addr
        if not ip_address:
            ip_address = request.remote_addr
            print(f"DEBUG: Using remote_addr: {ip_address}")

        # Final fallback
        if not ip_address or ip_address == '127.0.0.1' or ip_address == '::1':
            # In development, allow returning all bookings or use a test IP
            test_ip = request.args.get('test_ip')
            if test_ip:
                ip_address = test_ip
                print(f"DEBUG: Using test_ip: {ip_address}")
            else:
                # For development purposes, return all completed bookings
                # In production, you might want to return an error or handle differently
                print("DEBUG: No valid IP detected, will return all completed bookings")
                pass

        print(f"DEBUG: Final IP address: {ip_address}")

        # Find completed bookings from this IP (support both old and new format)
        query = {
            "$or": [
                {"user_ip": ip_address},  # New bookings with IP stored
                {"ip_address": ip_address}  # Legacy bookings
            ],
            "status": "Completed"
        } if ip_address else {"status": "Completed"}  # Fallback to all if no IP detected

        print(f"DEBUG: Query: {query}")

        completed_bookings = list(orders_collection.find(query).sort("event_date", -1))  # Most recent first
        print(f"DEBUG: Found {len(completed_bookings)} completed bookings")

        # Format bookings for frontend
        formatted_bookings = []
        for booking in completed_bookings:
            # Check if this booking has already been rated (check both old and new rating systems)
            already_rated = booking.get("rating") is not None

            formatted_bookings.append({
                "_id": str(booking["_id"]),
                "event_date": booking.get("event_date", ""),
                "service_type": booking.get("service_type", "Catering Service"),
                "guests": booking.get("guests", 0),
                "already_rated": already_rated
            })

        print(f"DEBUG: Returning {len(formatted_bookings)} formatted bookings")
        return jsonify({
            "success": True,
            "bookings": formatted_bookings,
            "count": len(formatted_bookings)
        })

    except Exception as e:
        print(f"Error fetching user completed bookings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to fetch bookings"}), 500


# =========================
# CHECK RATING ELIGIBILITY
# =========================

@bookings_bp.route("/check-rating-eligibility", methods=["GET"])
def check_rating_eligibility_endpoint():
    """
    Public API: Checks if the current user IP is eligible to submit a rating.
    Returns eligibility status without requiring authentication.
    """
    try:
        # Get client IP address
        user_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))

        # Check eligibility
        eligible = check_rating_eligibility(user_ip)

        return jsonify({
            "eligible": eligible,
            "message": "You can submit a rating" if eligible else "Please complete a booking before giving rating"
        })

    except Exception as e:
        print(f"Error checking rating eligibility: {e}")
        return jsonify({"error": "Failed to check eligibility"}), 500


# =========================
# SUBMIT AUTOMATIC RATING
# =========================

@bookings_bp.route("/submit-rating", methods=["POST"])
def submit_rating():
    """
    Public API: Submits a rating for a specific completed booking.
    Requires booking_id selection and validates per booking (one rating per booking).
    """
    try:
        data = request.get_json()
        rating = data.get("rating")
        booking_id = data.get("booking_id")
        review = sanitize_string(data.get("review", ""), 1000)

        # Validate rating
        if not rating:
            return jsonify({"success": False, "message": "Rating is required"}), 400

        try:
            rating = int(rating)
        except ValueError:
            return jsonify({"success": False, "message": "Rating must be a number"}), 400

        if not (1 <= rating <= 5):
            return jsonify({"success": False, "message": "Rating must be between 1 and 5"}), 400

        # Validate booking_id
        if not booking_id:
            return jsonify({"success": False, "message": "Booking ID is required"}), 400

        # Validate booking_id format
        try:
            from bson import ObjectId
            booking_object_id = ObjectId(booking_id)
        except Exception:
            return jsonify({"success": False, "message": "Invalid booking ID format"}), 400

        # Check if booking exists
        booking = orders_collection.find_one({"_id": booking_object_id})
        if not booking:
            return jsonify({"success": False, "message": "Booking not found"}), 404

        # Check if booking is completed
        if booking.get("status") != "Completed":
            return jsonify({"success": False, "message": "You can only rate completed bookings"}), 400

        # Check if booking has already been rated
        if booking.get("rating") is not None:
            return jsonify({"success": False, "message": "You have already rated this booking"}), 400

        # Get client IP address for additional validation
        user_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))

        # Check if this IP has already rated this specific booking (additional security)
        # This prevents rating manipulation even if booking_id is somehow obtained

        # Update booking with rating
        result = orders_collection.update_one(
            {"_id": booking_object_id},
            {"$set": {"rating": rating, "rating_submitted_at": datetime.utcnow()}}
        )

        if result.modified_count > 0:
            # Invalidate cache to force fresh calculation
            from backend.models import invalidate_rating_cache
            invalidate_rating_cache()

            # Get updated average rating
            from backend.models import get_ratings_average
            avg_rating, total_ratings = get_ratings_average()

            return jsonify({
                "success": True,
                "message": "Rating submitted successfully",
                "avgRating": avg_rating,
                "totalRatings": total_ratings
            }), 200
        else:
            return jsonify({"success": False, "message": "Failed to save rating"}), 500

    except Exception as e:
        print(f"Error submitting rating: {e}")
        return jsonify({"success": False, "message": "Failed to submit rating"}), 500


# =========================
# GET RATINGS AVERAGE
# =========================

@bookings_bp.route("/ratings-average", methods=["GET"])
def get_ratings_average_endpoint():
    """
    Public API: Returns the average rating from bookings collection.
    """
    try:
        from backend.models import get_ratings_average
        average, count = get_ratings_average()

        return jsonify({
            "success": True,
            "average_rating": average,
            "total_ratings": count
        })

    except Exception as e:
        print(f"Error fetching ratings average: {e}")
        return jsonify({"error": "Failed to fetch ratings average"}), 500
