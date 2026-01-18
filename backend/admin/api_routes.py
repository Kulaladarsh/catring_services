from flask import Blueprint, request, jsonify, session
from backend.models import (
    get_all_bookings,
    get_booking_by_id,
    update_booking_status,
    mark_ingredients_sent,
    log_admin_action
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
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return wrapper


# =========================
# STATS ENDPOINT
# =========================

@admin_api_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """
    Admin API: Returns dashboard statistics
    """
    try:
        from backend.db import orders_collection, dishes_collection

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

        return jsonify({
            "total_orders": total_orders,
            "active_dishes": active_dishes,
            "revenue": total_revenue,
            "pending_orders": pending_orders
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
