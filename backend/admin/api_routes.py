# File: backend/admin/api_routes.py
# ✅ FIXED: Rating endpoint now works with real booking IDs and removes status validation

from flask import Blueprint, request, jsonify, session
from backend.models import (
    get_all_bookings,
    get_booking_by_id,
    update_booking_status,
    mark_ingredients_sent,
    log_admin_action,
    get_average_rating,
    update_booking_rating,
    get_ratings_average,
    submit_automatic_rating,
    submit_user_rating
)
from backend.utils.email import send_ingredients_list
from backend.utils.whatsapp import send_ingredients_whatsapp
from functools import wraps
from bson import ObjectId
from backend.db import orders_collection, final_ingredients_collection

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/admin/api')

# =========================
# DECORATOR: ADMIN REQUIRED
# =========================

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return jsonify({"success": False, "message": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return wrapper


# =========================
# STATS ENDPOINT
# =========================

@admin_api_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """
    Admin API: Returns dashboard statistics including chart data
    """
    try:
        from backend.db import orders_collection, dishes_collection
        from datetime import datetime, timedelta
        from collections import defaultdict

        if orders_collection is None or dishes_collection is None:
            return jsonify({"error": "Database not available"}), 500

        # Get total orders
        total_orders = orders_collection.count_documents({})

        # Get active dishes
        active_dishes = dishes_collection.count_documents({"is_active": True})

        # Get total revenue
        orders = list(orders_collection.find({}))
        total_revenue = sum(order.get('pricing', {}).get('total', 0) for order in orders)

        # Get pending orders
        pending_orders = orders_collection.count_documents({"status": "Pending"})

        # Get active users (unique customers with orders in last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_orders = orders_collection.find({
            "created_at": {"$gte": thirty_days_ago}
        })
        active_users = len(set(order.get('email', '') for order in recent_orders if order.get('email')))

        # Monthly earnings for the last 12 months
        monthly_earnings = []
        for i in range(11, -1, -1):
            month_date = datetime.now() - timedelta(days=i*30)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            month_orders = orders_collection.find({
                "created_at": {"$gte": month_start, "$lte": month_end}
            })

            month_revenue = sum(order.get('pricing', {}).get('total', 0) for order in month_orders)
            monthly_earnings.append({
                "month": month_start.strftime("%b %Y"),
                "earnings": month_revenue
            })

        # Order status distribution
        status_counts = defaultdict(int)
        for order in orders:
            status = order.get('status', 'Unknown').lower()
            status_counts[status] += 1

        order_status_stats = [
            {"status": status.title(), "count": count}
            for status, count in status_counts.items()
        ]

        # Daily visitors for the last 30 days (using order creation dates as proxy)
        daily_visitors = []
        for i in range(29, -1, -1):
            date = datetime.now() - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

            day_orders = orders_collection.count_documents({
                "created_at": {"$gte": date_start, "$lte": date_end}
            })

            daily_visitors.append({
                "date": date.strftime("%Y-%m-%d"),
                "visitors": day_orders  # Using orders as proxy for visitors
            })

        return jsonify({
            "total_orders": total_orders,
            "active_dishes": active_dishes,
            "revenue": total_revenue,
            "pending_orders": pending_orders,
            "active_users": active_users,
            "monthly_earnings": monthly_earnings,
            "order_status_stats": order_status_stats,
            "daily_visitors": daily_visitors
        })

    except Exception as e:
        return jsonify({"error": f"Failed to fetch stats: {str(e)}"}), 500


# =========================
# BOOKINGS ENDPOINT
# =========================

@admin_api_bp.route('/bookings', methods=['GET'])
@admin_required
def get_bookings():
    """
    Admin API: Returns all bookings with optional filters
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

    try:
        bookings = get_all_bookings(filters if filters else None)

        return jsonify({
            "success": True,
            "bookings": bookings,
            "count": len(bookings)
        })

    except Exception as e:
        return jsonify({"error": f"Failed to fetch bookings: {str(e)}"}), 500


# =========================
# SINGLE BOOKING ENDPOINT
# =========================

@admin_api_bp.route('/bookings/<booking_id>', methods=['GET'])
@admin_required
def get_booking(booking_id):
    """
    Admin API: Returns details of a single booking
    """
    try:
        booking = get_booking_by_id(booking_id)

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        return jsonify({
            "success": True,
            "booking": booking
        })

    except Exception as e:
        return jsonify({"error": f"Failed to fetch booking: {str(e)}"}), 500


# =========================
# UPDATE BOOKING STATUS
# =========================

@admin_api_bp.route('/bookings/<booking_id>/status', methods=['PATCH'])
@admin_required
def update_booking_status_endpoint(booking_id):
    """
    Admin API: Updates booking status
    """
    data = request.get_json()
    status = data.get("status")

    valid_statuses = ["Pending", "Confirmed", "Completed", "Cancelled"]
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    try:
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

    except Exception as e:
        return jsonify({"error": f"Failed to update status: {str(e)}"}), 500


# =========================
# SEND INGREDIENTS
# =========================

@admin_api_bp.route('/bookings/<booking_id>/send-ingredients', methods=['POST'])
@admin_required
def send_ingredients(booking_id):
    """
    Admin API: Sends ingredients list to customer
    """
    data = request.get_json()
    ingredients = data.get("ingredients")

    if not ingredients:
        return jsonify({"error": "Ingredients list is required"}), 400

    try:
        # Get booking details
        booking = get_booking_by_id(booking_id)
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

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


# =========================
# BOOKING INGREDIENTS ENDPOINT
# =========================

@admin_api_bp.route('/bookings/<booking_id>/ingredients', methods=['GET'])
@admin_required
def get_booking_ingredients(booking_id):
    """
    Admin API: Returns aggregated ingredients for a booking
    """
    try:
        # Get booking details
        booking = get_booking_by_id(booking_id)
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # Simple aggregation for now - return empty ingredients
        # This can be enhanced later with proper ingredient aggregation
        ingredients = []

        return jsonify({
            "booking_id": booking_id,
            "customer_name": booking["customer_name"],
            "guests": booking["guests"],
            "ingredients": ingredients
        })

    except Exception as e:
        return jsonify({"error": f"Failed to fetch ingredients: {str(e)}"}), 500


# =========================
# DELETE BOOKING ENDPOINT
# =========================

@admin_api_bp.route('/bookings/<booking_id>', methods=['DELETE'])
@admin_required
def delete_booking(booking_id):
    """
    ✅ NEW: Delete completed order
    """
    try:
        # Check if booking exists and is completed
        booking = get_booking_by_id(booking_id)
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        if booking.get('status') not in ['Completed', 'Cancelled']:
            return jsonify({
                "error": "Only completed or cancelled orders can be deleted"
            }), 400

        # Delete booking
        result = orders_collection.delete_one({"_id": ObjectId(booking_id)})

        if result.deleted_count > 0:
            # Also delete associated final ingredients
            final_ingredients_collection.delete_one({"booking_id": booking_id})

            # Log action
            username = session.get("admin_username")
            log_admin_action(username, f"ORDER_DELETED: {booking_id}")

            return jsonify({
                "success": True,
                "message": "Order deleted successfully"
            })
        else:
            return jsonify({"error": "Delete failed"}), 500

    except Exception as e:
        return jsonify({"error": f"Failed to delete order: {str(e)}"}), 500


# =========================
# ✅ FIXED RATING ENDPOINTS
# =========================

@admin_api_bp.route('/average-rating', methods=['GET'])
def get_average_rating_endpoint():
    """
    Public API: Returns the average rating from the automatic ratings system
    """
    try:
        average, count = get_ratings_average()

        return jsonify({
            "success": True,
            "average_rating": average,
            "total_ratings": count
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch average rating: {str(e)}"}), 500


@admin_api_bp.route('/rate-booking/<booking_id>', methods=['POST'])
def rate_booking(booking_id):
    """
    ✅ FIXED: Public API for rating bookings
    - Accepts real MongoDB ObjectId booking IDs
    - No longer requires "Completed" status
    - Allows rating immediately after booking
    """
    try:
        from backend.db import orders_collection
        from bson import ObjectId
        from datetime import datetime

        data = request.get_json()
        rating = data.get("rating")

        # Validate rating
        if not rating:
            return jsonify({"success": False, "message": "Rating is required"}), 400

        try:
            rating = int(rating)
        except ValueError:
            return jsonify({"success": False, "message": "Rating must be a number"}), 400

        if not (1 <= rating <= 5):
            return jsonify({"success": False, "message": "Rating must be between 1 and 5"}), 400

        # Validate booking ID format
        try:
            booking_object_id = ObjectId(booking_id)
        except Exception:
            return jsonify({"success": False, "message": "Invalid booking ID format"}), 400

        # Check if booking exists
        booking = orders_collection.find_one({"_id": booking_object_id})
        if not booking:
            return jsonify({"success": False, "message": "Booking not found"}), 404

        # Check if already rated
        if booking.get("rating") is not None:
            return jsonify({"success": False, "message": "Booking already rated"}), 400

        # Save rating
        result = orders_collection.update_one(
            {"_id": booking_object_id},
            {"$set": {"rating": rating, "updated_at": datetime.utcnow()}}
        )

        if result.modified_count > 0:
            return jsonify({
                "success": True,
                "message": "Rating submitted successfully"
            }), 200
        else:
            return jsonify({"success": False, "message": "Failed to save rating"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to submit rating: {str(e)}"}), 500


# =========================
# SUBMIT USER RATING ENDPOINT
# =========================

@admin_api_bp.route('/submit-user-rating', methods=['POST'])
def submit_user_rating_endpoint():
    """
    Public API: Submits a user rating linked to a completed booking
    - No authentication required
    - Rating must be linked to a completed booking ID
    - One rating per completed booking
    - Prevents duplicate ratings for same booking
    """
    try:
        from datetime import datetime
        data = request.get_json()
        rating = data.get("rating")
        booking_id = data.get("booking_id")
        user_agent = data.get("user_agent")

        # Validate rating
        if not rating:
            return jsonify({"success": False, "message": "Rating is required"}), 400

        try:
            rating = int(rating)
        except ValueError:
            return jsonify({"success": False, "message": "Rating must be a number"}), 400

        if not (1 <= rating <= 5):
            return jsonify({"success": False, "message": "Rating must be between 1 and 5"}), 400

        # Validate booking_id is required
        if not booking_id:
            return jsonify({"success": False, "message": "Booking ID is required"}), 400

        # Validate booking_id format
        try:
            from bson import ObjectId
            booking_object_id = ObjectId(booking_id)
        except Exception:
            return jsonify({"success": False, "message": "Invalid booking ID format"}), 400

        # Check if booking exists
        from backend.db import orders_collection
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
        ip_address = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))

        # Optional mobile number (not required)
        mobile = data.get("mobile", "").strip()

        # Submit rating using the model function (will store in user_ratings_collection)
        success = submit_user_rating(mobile, ip_address, rating, user_agent)

        if success:
            # Update the booking with the rating
            result = orders_collection.update_one(
                {"_id": booking_object_id},
                {"$set": {"rating": rating, "rating_submitted_at": datetime.utcnow()}}
            )

            if result.modified_count > 0:
                return jsonify({
                    "success": True,
                    "message": "Rating submitted successfully"
                }), 200
            else:
                return jsonify({"success": False, "message": "Failed to save rating to booking"}), 500
        else:
            return jsonify({"success": False, "message": "Failed to submit rating"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to submit rating: {str(e)}"}), 500
