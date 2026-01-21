from flask import Blueprint, request, jsonify, session
from backend.db import dishes_collection
from backend.models import log_admin_action
from functools import wraps
from bson import ObjectId
from datetime import datetime

admin_dishes_bp = Blueprint("admin_dishes", __name__, url_prefix="/admin/api/dishes")

# =========================
# DECORATOR: ADMIN REQUIRED
# =========================

def admin_required(f):
    """
    Decorator for API routes requiring admin authentication.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return wrapper


# =========================
# HELPER FUNCTIONS
# =========================

def normalize_meal_type(value):
    """
    Normalizes meal_type to 'veg' or 'nonveg'
    """
    if not value:
        return "veg"
    
    value = str(value).lower().strip()
    
    # Handle various input formats
    if value in ["nonveg", "non-veg", "non veg", "chicken", "mutton", "fish", "egg", "non_veg"]:
        return "nonveg"
    else:
        return "veg"


def get_request_data():
    """
    Safely extracts data from either JSON or FormData
    """
    # Try JSON first
    if request.is_json:
        return request.get_json()
    
    # Try form data
    if request.form:
        data = {}
        for key in request.form.keys():
            value = request.form[key]
            # Convert string booleans to actual booleans
            if value.lower() in ['true', 'false']:
                data[key] = value.lower() == 'true'
            else:
                data[key] = value
        return data
    
    # Try to get JSON from request.data
    try:
        import json
        return json.loads(request.data)
    except:
        return {}


def format_dish_for_response(dish):
    """
    Formats a dish document for API response
    """
    return {
        "_id": str(dish["_id"]),
        "name": dish.get("name", ""),
        "price": float(dish.get("price", 0)),
        "meal_type": dish.get("meal_type", "veg").lower(),
        "category": dish.get("category", "General"),
        "image_url": dish.get("image_url", ""),
        "description": dish.get("description", ""),
        "ingredients": dish.get("ingredients", []),
        "available": bool(dish.get("available", True)),
        "is_active": bool(dish.get("is_active", True)),
        "created_at": dish.get("created_at"),
        "updated_at": dish.get("updated_at")
    }


def validate_ingredients(ingredients):
    """
    Validates ingredient data structure
    """
    if not isinstance(ingredients, list):
        return False

    valid_units = ["g", "kg", "oz", "lb", "mg", "ml", "l", "litre", "cup", "tbsp", "tsp", "pcs", "packet", "bunch", "dozen", "slice", "can", "bottle"]
    valid_categories = ["Vegetables", "Non-Vegetarian", "Spices / Masala", "Dairy", "Fruit", "Dry Fruits", "Grain", "Herbs", "Beverages", "Oil and Fats", "Bakery & Sweets", "Other"]

    for ing in ingredients:
        if not isinstance(ing, dict):
            return False
        if not ing.get("name", "").strip():
            return False
        if not isinstance(ing.get("per_plate", 0), (int, float)) or ing["per_plate"] <= 0:
            return False
        if ing.get("unit", "").strip() not in valid_units:
            return False
        if ing.get("category", "").strip() not in valid_categories:
            return False

    return True


# =========================
# ADMIN API - GET ALL DISHES
# =========================

@admin_dishes_bp.route("/", methods=["GET"])
@admin_required
def get_all_dishes():
    """
    ADMIN API: Returns all dishes (including inactive ones)
    """
    try:
        if dishes_collection is None:
            return jsonify({"success": False, "error": "Database not available"}), 500

        dishes = list(dishes_collection.find({}))
        formatted_dishes = [format_dish_for_response(dish) for dish in dishes]

        return jsonify(formatted_dishes)

    except Exception as e:
        print(f"Error in get_all_dishes: {str(e)}")
        return jsonify({"error": str(e)}), 500


# =========================
# ADMIN API - CREATE DISH
# =========================

@admin_dishes_bp.route("/", methods=["POST"])
@admin_required
def create_dish():
    """
    ADMIN API: Creates a new dish.
    
    Accepts BOTH JSON and FormData
    
    Request body:
    {
        "name": "Dish name" (required),
        "category": "veg" or "nonveg" (required),
        "price": 150.0 (required),
        "image_url": "URL or filename" (optional),
        "description": "Description" (optional),
        "available": true (optional, default: true)
    }
    """
    try:
        data = get_request_data()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        name = data.get("name", "").strip()
        price = data.get("price")
        category = data.get("category", "veg")
        
        if not name:
            return jsonify({"error": "Dish name is required"}), 400
        
        if not price or float(price) <= 0:
            return jsonify({"error": "Valid price is required"}), 400
        
        # Check for duplicate dish name (case-insensitive)
        existing_dish = dishes_collection.find_one({
            "name": {"$regex": f"^{name}$", "$options": "i"}
        })
        
        if existing_dish:
            return jsonify({"error": f"Dish '{name}' already exists"}), 400
        
        # Normalize meal_type
        meal_type = normalize_meal_type(category)
        
        # Parse boolean fields
        available = data.get("available", True)
        if isinstance(available, str):
            available = available.lower() in ['true', '1', 'yes']
        available = bool(available)

        # Validate and parse ingredients
        ingredients = data.get("ingredients", [])
        if ingredients and not validate_ingredients(ingredients):
            return jsonify({"error": "Invalid ingredients format. Each ingredient must have name, per_plate (number > 0), unit (kg/gm/litre/pcs), and category (Vegetables/Non-Vegetarian/Spices/Others)"}), 400

        # Create dish document
        dish = {
            "name": name,
            "meal_type": meal_type,
            "category": data.get("category", "General"),
            "price": float(price),
            "image_url": data.get("image_url", "").strip(),
            "description": data.get("description", "").strip(),
            "ingredients": ingredients,  # Array of {name, per_plate, unit, category}
            "available": available,
            "is_active": True,
            "is_signature": True,  # All new dishes are automatically signature dishes
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = dishes_collection.insert_one(dish)
        dish_id = str(result.inserted_id)
        
        # Log admin action
        username = session.get("admin_username", "admin")
        log_admin_action(username, f"DISH_CREATED: {name}")
        
        return jsonify({
            "success": True,
            "message": "Dish added successfully",
            "dish_id": dish_id
        }), 201
        
    except ValueError as ve:
        return jsonify({"error": f"Invalid data format: {str(ve)}"}), 400
    except Exception as e:
        print(f"Error creating dish: {str(e)}")
        return jsonify({"error": str(e)}), 500


# =========================
# ADMIN API - UPDATE DISH
# =========================

@admin_dishes_bp.route("/<dish_id>", methods=["PUT", "PATCH"])
@admin_required
def update_dish(dish_id):
    """
    ADMIN API: Updates an existing dish.
    
    Request body (all fields optional):
    {
        "name": "Updated name",
        "category": "veg",
        "price": 200.0,
        "image_url": "new_url",
        "description": "new description",
        "available": false
    }
    """
    try:
        data = get_request_data()
        
        if not data:
            return jsonify({"error": "No update data provided"}), 400
        
        # Check if dish exists
        existing_dish = dishes_collection.find_one({"_id": ObjectId(dish_id)})
        if not existing_dish:
            return jsonify({"error": "Dish not found"}), 404
        
        # Build update document
        update_data = {"updated_at": datetime.utcnow()}
        
        if "name" in data:
            name = data["name"].strip()
            if name:
                # Check for duplicate name (excluding current dish)
                duplicate = dishes_collection.find_one({
                    "name": {"$regex": f"^{name}$", "$options": "i"},
                    "_id": {"$ne": ObjectId(dish_id)}
                })
                if duplicate:
                    return jsonify({"error": f"Dish '{name}' already exists"}), 400
                update_data["name"] = name
        
        if "price" in data:
            update_data["price"] = float(data["price"])
        
        if "category" in data:
            update_data["meal_type"] = normalize_meal_type(data["category"])
            update_data["category"] = data["category"]
        
        if "image_url" in data:
            update_data["image_url"] = data["image_url"].strip()
        
        if "description" in data:
            update_data["description"] = data["description"].strip()
        
        if "available" in data:
            available = data["available"]
            if isinstance(available, str):
                available = available.lower() in ['true', '1', 'yes']
            update_data["available"] = bool(available)

        if "is_signature" in data:
            update_data["is_signature"] = bool(data["is_signature"])
        
        # Update dish
        result = dishes_collection.update_one(
            {"_id": ObjectId(dish_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            username = session.get("admin_username", "admin")
            log_admin_action(username, f"DISH_UPDATED: {existing_dish['name']}")
            
            return jsonify({
                "success": True,
                "message": "Dish updated successfully"
            })
        else:
            return jsonify({
                "success": True,
                "message": "No changes made"
            })
        
    except Exception as e:
        print(f"Error updating dish: {str(e)}")
        return jsonify({"error": str(e)}), 500


# =========================
# ADMIN API - DELETE DISH
# =========================

@admin_dishes_bp.route("/<dish_id>", methods=["DELETE"])
@admin_required
def delete_dish(dish_id):
    """
    ADMIN API: Deletes a dish permanently.
    """
    try:
        # Check if dish exists
        existing_dish = dishes_collection.find_one({"_id": ObjectId(dish_id)})
        if not existing_dish:
            return jsonify({"error": "Dish not found"}), 404
        
        result = dishes_collection.delete_one({"_id": ObjectId(dish_id)})
        
        if result.deleted_count > 0:
            username = session.get("admin_username", "admin")
            log_admin_action(username, f"DISH_DELETED: {existing_dish['name']}")
            
            return jsonify({
                "success": True,
                "message": "Dish deleted successfully"
            })
        else:
            return jsonify({"error": "Delete failed"}), 500
        
    except Exception as e:
        print(f"Error deleting dish: {str(e)}")
        return jsonify({"error": str(e)}), 500


# =========================
# ADMIN API - TOGGLE DISH STATUS
# =========================

@admin_dishes_bp.route("/<dish_id>/toggle", methods=["PATCH"])
@admin_required
def toggle_dish_status(dish_id):
    """
    ADMIN API: Toggles dish active/inactive status.
    """
    try:
        dish = dishes_collection.find_one({"_id": ObjectId(dish_id)})
        
        if not dish:
            return jsonify({"error": "Dish not found"}), 404
        
        new_status = not dish.get("is_active", True)
        
        result = dishes_collection.update_one(
            {"_id": ObjectId(dish_id)},
            {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            username = session.get("admin_username", "admin")
            status_text = "ENABLED" if new_status else "DISABLED"
            log_admin_action(username, f"DISH_{status_text}: {dish['name']}")
            
            return jsonify({
                "success": True,
                "message": f"Dish {'enabled' if new_status else 'disabled'} successfully",
                "is_active": new_status
            })
        else:
            return jsonify({"error": "Status update failed"}), 500
        
    except Exception as e:
        print(f"Error toggling dish status: {str(e)}")
        return jsonify({"error": str(e)}), 500