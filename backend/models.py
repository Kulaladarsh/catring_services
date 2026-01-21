from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .db import (
    admins_collection,
    admin_logs_collection,
    dishes_collection,
    orders_collection,
    reserved_slots_collection
)
from bson import ObjectId

# =========================
# ADMIN AUTHENTICATION
# =========================

def create_admin(username, password):
    """
    Creates a new admin user with hashed password.
    ⚠️ Call ONLY from Python shell for initial setup.
    
    Usage:
        from backend.models import create_admin
        create_admin("Admin", "Chetan@23001867")
    """
    
    if admins_collection.find_one({"username": username}):
        print("❌ Admin already exists")
        return False
    
    admins_collection.insert_one({
        "username": username,
        "password": generate_password_hash(password),
        "created_at": datetime.utcnow(),
        "login_attempts": 0,
        "locked_until": None
    })
    
    print(f"✅ Admin '{username}' created successfully")
    return True


def validate_admin(username, password):
    """
    Validates admin login credentials.
    Returns:
        True: Login successful
        False: Invalid credentials
        "LOCKED": Account locked due to failed attempts
    """
    admin = admins_collection.find_one({"username": username})
    
    if not admin:
        return False
    
    # Check if account is locked
    if admin.get("locked_until") and datetime.utcnow() < admin["locked_until"]:
        return "LOCKED"
    
    # Verify password
    if check_password_hash(admin["password"], password):
        # Reset login attempts on successful login
        admins_collection.update_one(
            {"username": username},
            {"$set": {"login_attempts": 0, "locked_until": None}}
        )
        log_admin_action(username, "LOGIN_SUCCESS")
        return True
    
    # Increment failed login attempts
    attempts = admin.get("login_attempts", 0) + 1
    update = {"login_attempts": attempts}
    
    # Lock account after 5 failed attempts
    if attempts >= 5:
        update["locked_until"] = datetime.utcnow() + timedelta(minutes=15)
    
    admins_collection.update_one(
        {"username": username}, 
        {"$set": update}
    )
    log_admin_action(username, "LOGIN_FAILED")
    
    return False


def log_admin_action(username, action):
    """
    Logs admin actions for audit trail.
    """
    admin_logs_collection.insert_one({
        "username": username,
        "action": action,
        "timestamp": datetime.utcnow()
    })


# =========================
# DISH MANAGEMENT
# =========================

def create_dish(name, category, price, image_url, is_active=True, is_signature=False):
    """
    Creates a new dish in the database.

    Args:
        name: Dish name
        category: "veg" or "nonveg"
        price: Price per plate
        image_url: URL or filename of dish image
        is_active: Whether dish is available for ordering
        is_signature: Whether this is a signature dish
    """
    dish = {
        "name": name,
        "category": category.lower(),
        "price": float(price),
        "image_url": image_url,
        "is_active": is_active,
        "is_signature": is_signature,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = dishes_collection.insert_one(dish)
    return str(result.inserted_id)


def get_all_dishes(only_active=False):
    """
    Retrieves all dishes from database.
    
    Args:
        only_active: If True, returns only active dishes
    """
    query = {"is_active": True} if only_active else {}
    dishes = list(dishes_collection.find(query))
    
    # Convert ObjectId to string for JSON serialization
    for dish in dishes:
        dish["_id"] = str(dish["_id"])
    
    return dishes


def get_dish_by_id(dish_id):
    """
    Retrieves a single dish by ID.
    """
    try:
        dish = dishes_collection.find_one({"_id": ObjectId(dish_id)})
        if dish:
            dish["_id"] = str(dish["_id"])
        return dish
    except:
        return None


def update_dish(dish_id, update_data):
    """
    Updates dish information.
    """
    try:
        update_data["updated_at"] = datetime.utcnow()
        result = dishes_collection.update_one(
            {"_id": ObjectId(dish_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except:
        return False


def delete_dish(dish_id):
    """
    Deletes a dish from database.
    """
    try:
        result = dishes_collection.delete_one({"_id": ObjectId(dish_id)})
        return result.deleted_count > 0
    except:
        return False


# =========================
# BOOKING MANAGEMENT
# =========================

def check_slot_availability(date, time_slot):
    """
    Checks if a time slot is available for booking.
    
    Args:
        date: Event date (string format: YYYY-MM-DD)
        time_slot: "Morning", "Afternoon", or "Night"
    
    Returns:
        True if available, False if already booked
    """
    existing = reserved_slots_collection.find_one({
        "date": date,
        "time_slot": time_slot
    })
    
    return existing is None


def create_booking(booking_data):
    """
    Creates a new booking and reserves the time slot.
    
    Args:
        booking_data: Dictionary containing:
            - customer_name
            - mobile
            - email
            - event_location
            - map_link
            - service_type
            - event_date
            - time_slot
            - guests
            - selected_dishes (list of {dish_id, quantity})
            - food_preference
    
    Returns:
        booking_id if successful, None if slot already booked
    """
    
    # Check slot availability first
    if not check_slot_availability(booking_data["event_date"], booking_data["time_slot"]):
        return None
    
    # Calculate price breakdown
    subtotal = 0
    dish_details = []
    
    for item in booking_data["selected_dishes"]:
        dish = get_dish_by_id(item["dish_id"])
        if dish:
            item_total = dish["price"] * item["quantity"]
            subtotal += item_total
            dish_details.append({
                "dish_id": item["dish_id"],
                "dish_name": dish["name"],
                "quantity": item["quantity"],
                "price_per_plate": dish["price"],
                "total": item_total
            })
    
    service_charge = subtotal * 0.10  # 10%
    gst = (subtotal + service_charge) * 0.05  # 5%
    total = subtotal + service_charge + gst
    
    # Create booking document
    booking = {
        "customer_name": booking_data["customer_name"],
        "mobile": booking_data["mobile"],
        "email": booking_data["email"],
        "event_location": booking_data["event_location"],
        "map_link": booking_data.get("map_link", ""),
        "service_type": booking_data["service_type"],
        "event_date": booking_data["event_date"],
        "time_slot": booking_data["time_slot"],
        "guests": booking_data["guests"],
        "food_preference": booking_data["food_preference"],
        "dishes": dish_details,
        "pricing": {
            "subtotal": round(subtotal, 2),
            "service_charge": round(service_charge, 2),
            "gst": round(gst, 2),
            "total": round(total, 2)
        },
        "status": "Pending",
        "ingredients_sent": False,
        "rating": None,  # Rating from 1-5 stars, submitted after booking completion
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert order
    result = orders_collection.insert_one(booking)
    booking_id = str(result.inserted_id)

    # Reserve the time slot
    reserved_slots_collection.insert_one({
        "date": booking_data["event_date"],
        "time_slot": booking_data["time_slot"],
        "booking_id": booking_id,
        "reserved_at": datetime.utcnow()
    })
    
    return booking_id


def get_all_bookings(filters=None):
    """
    Retrieves all orders with optional filters.

    Args:
        filters: Dictionary of filter conditions
    """
    query = filters if filters else {}
    orders = list(orders_collection.find(query).sort("created_at", -1))

    for order in orders:
        order["_id"] = str(order["_id"])

    return orders


def get_booking_by_id(booking_id):
    """
    Retrieves a single order by ID.
    """
    try:
        order = orders_collection.find_one({"_id": ObjectId(booking_id)})
        if order:
            order["_id"] = str(order["_id"])
        return order
    except:
        return None


def update_booking_status(booking_id, status):
    """
    Updates order status.

    Args:
        status: "Pending", "Confirmed", "Completed", "Cancelled"
    """
    try:
        result = orders_collection.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    except:
        return False


def mark_ingredients_sent(booking_id):
    """
    Marks that ingredients list has been sent to customer.
    """
    try:
        result = orders_collection.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {"ingredients_sent": True, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    except:
        return False


def update_booking_rating(booking_id, rating):
    """
    Updates the rating for a booking.

    Args:
        booking_id: The booking ID
        rating: Rating from 1-5 stars

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        if not (1 <= rating <= 5):
            return False
        result = orders_collection.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {"rating": rating, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    except:
        return False


def get_average_rating():
    """
    Calculates the average rating from all rated bookings.

    Returns:
        Average rating (float) or None if no ratings
    """
    try:
        pipeline = [
            {"$match": {"rating": {"$ne": None}}},
            {"$group": {"_id": None, "average": {"$avg": "$rating"}, "count": {"$sum": 1}}}
        ]
        result = list(orders_collection.aggregate(pipeline))
        if result:
            return round(result[0]["average"], 1), result[0]["count"]
        return None, 0
    except:
        return None, 0
