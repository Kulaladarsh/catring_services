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

bookings_bp = Blueprint("bookings", __name__, url_prefix="/api/bookings")

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
    
    Request body (JSON):
    {
        "date": "2026-02-15",
        "time_slot": "Morning"
    }
    """
    data = request.get_json()
    
    date = data.get("date")
    time_slot = data.get("time_slot")
    
    if not date or not time_slot:
        return jsonify({"error": "Date and time_slot are required"}), 400
    
    # Validate date is not in the past
    try:
        event_date = datetime.strptime(date, "%Y-%m-%d")
        if event_date.date() < datetime.now().date():
            return jsonify({
                "available": False,
                "message": "Cannot book past dates"
            })
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
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
    
    Response:
    {
        "date": "2026-02-15",
        "available_slots": ["Morning", "Night"],
        "booked_slots": ["Afternoon"]
    }
    """
    try:
        # Validate date format
        event_date = datetime.strptime(date, "%Y-%m-%d")
        if event_date.date() < datetime.now().date():
            return jsonify({
                "error": "Cannot check past dates",
                "available_slots": [],
                "booked_slots": []
            })
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
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
    Returns dates where all slots are booked (fully booked dates).
    
    Response:
    {
        "success": true,
        "fully_booked_dates": ["2026-02-15", "2026-02-20"],
        "partially_booked_dates": [
            {
                "date": "2026-02-16",
                "booked_slots": ["Morning"],
                "available_slots": ["Afternoon", "Night"]
            }
        ]
    }
    """
    try:
        # Get all reserved slots grouped by date
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

        # Process results to identify fully booked dates
        fully_booked_dates = []
        partially_booked_dates = []

        all_slots = ["Morning", "Afternoon", "Night"]

        for result in booked_dates_result:
            date = result["_id"]
            booked_slots = result["booked_slots"]

            # Skip past dates
            try:
                event_date = datetime.strptime(date, "%Y-%m-%d")
                if event_date.date() < datetime.now().date():
                    continue
            except:
                continue

            # Check if all 3 slots are booked
            if len(booked_slots) >= 3:  # All slots booked
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
# GET AVAILABILITY CALENDAR (30 DAYS)
# =========================

@bookings_bp.route("/availability-calendar", methods=["GET"])
def get_availability_calendar():
    """
    Public API: Returns availability status for next 30 days.
    Useful for calendar UI implementation.
    
    Response:
    {
        "calendar": [
            {
                "date": "2026-02-15",
                "status": "fully_booked",
                "available_slots": [],
                "booked_slots": ["Morning", "Afternoon", "Night"]
            },
            {
                "date": "2026-02-16",
                "status": "partially_available",
                "available_slots": ["Afternoon", "Night"],
                "booked_slots": ["Morning"]
            },
            {
                "date": "2026-02-17",
                "status": "available",
                "available_slots": ["Morning", "Afternoon", "Night"],
                "booked_slots": []
            }
        ]
    }
    """
    try:
        today = datetime.now().date()
        calendar_data = []
        all_slots = ["Morning", "Afternoon", "Night"]

        # Generate next 30 days
        for i in range(30):
            check_date = today + timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")

            available_slots = []
            booked_slots = []

            # Check each slot
            for slot in all_slots:
                if check_slot_availability(date_str, slot):
                    available_slots.append(slot)
                else:
                    booked_slots.append(slot)

            # Determine status
            if len(available_slots) == 0:
                status = "fully_booked"
            elif len(available_slots) == 3:
                status = "available"
            else:
                status = "partially_available"

            calendar_data.append({
                "date": date_str,
                "status": status,
                "available_slots": available_slots,
                "booked_slots": booked_slots,
                "available_count": len(available_slots)
            })

        return jsonify({
            "success": True,
            "calendar": calendar_data,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": f"Failed to generate calendar: {str(e)}"}), 500


# =========================
# CREATE BOOKING WITH VALIDATION
# =========================

@bookings_bp.route("/", methods=["POST"])
def create_new_booking():
    """
    Public API: Creates a new booking with real-time availability validation.
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = [
        "customer_name", "mobile", "email", "event_location",
        "service_type", "event_date", "time_slot", "guests",
        "food_preference", "selected_dishes"
    ]
    
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    
    # Validate date
    try:
        event_date = datetime.strptime(data["event_date"], "%Y-%m-%d")
        if event_date.date() < datetime.now().date():
            return jsonify({"error": "Cannot book past dates"}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    # Validate time slot
    valid_slots = ["Morning", "Afternoon", "Night"]
    if data["time_slot"] not in valid_slots:
        return jsonify({"error": f"Invalid time slot. Must be one of: {', '.join(valid_slots)}"}), 400
    
    # CRITICAL: Check availability immediately before creating booking
    if not check_slot_availability(data["event_date"], data["time_slot"]):
        return jsonify({
            "error": "This time slot is no longer available",
            "message": "The slot was booked by another user. Please select a different date or time slot.",
            "code": "SLOT_UNAVAILABLE"
        }), 409
    
    # Validate dishes
    if not data["selected_dishes"] or len(data["selected_dishes"]) == 0:
        return jsonify({"error": "At least one dish must be selected"}), 400
    
    # Create booking
    try:
        booking_id = create_booking(data)
        
        if not booking_id:
            return jsonify({
                "error": "Booking failed",
                "message": "Slot may have been booked by another user. Please try again.",
                "code": "BOOKING_FAILED"
            }), 409
        
        # Get complete booking details
        booking = get_booking_by_id(booking_id)
        
        # Send confirmation email to customer
        try:
            send_booking_confirmation(
                customer_email=data["email"],
                customer_name=data["customer_name"],
                booking_details=booking
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        # Send WhatsApp confirmation
        try:
            send_booking_confirmation_whatsapp(
                phone_number=data["mobile"],
                customer_name=data["customer_name"],
                booking_details=booking
            )
        except Exception as e:
            print(f"WhatsApp sending failed: {e}")
        
        # Notify admin
        try:
            send_admin_notification(booking)
        except Exception as e:
            print(f"Admin notification failed: {e}")
        
        return jsonify({
            "success": True,
            "message": "Booking created successfully",
            "booking_id": booking_id,
            "booking": booking
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Booking creation failed: {str(e)}"}), 500


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
    
    # Build filter query
    if request.args.get("date"):
        filters["event_date"] = request.args.get("date")
    
    if request.args.get("time_slot"):
        filters["time_slot"] = request.args.get("time_slot")
    
    if request.args.get("status"):
        filters["status"] = request.args.get("status")
    
    if request.args.get("service_type"):
        filters["service_type"] = request.args.get("service_type")
    
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
    data = request.get_json()
    status = data.get("status")
    
    valid_statuses = ["Pending", "Confirmed", "Completed", "Cancelled"]
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
    
    # Check if booking exists
    booking = get_booking_by_id(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    success = update_booking_status(booking_id, status)
    
    if success:
        username = session.get("admin_username")
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
    data = request.get_json()
    ingredients = data.get("ingredients")
    
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
        username = session.get("admin_username")
        log_admin_action(username, f"INGREDIENTS_SENT: {booking_id}")
        
        return jsonify({
            "success": True,
            "message": "Ingredients list sent successfully",
            "email_sent": email_sent,
            "whatsapp_sent": whatsapp_sent
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to send ingredients: {str(e)}"}), 500