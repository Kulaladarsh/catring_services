from flask import Blueprint, request, jsonify, session
from backend.db import dishes_collection
from backend.models import log_admin_action
from functools import wraps
from bson import ObjectId
from datetime import datetime
from backend.db import categories_collection


dishes_bp = Blueprint("dishes", __name__, url_prefix="/api/dishes")

# =========================
# DECORATOR: ADMIN REQUIRED
# =========================

def admin_required(f):
    """
    Decorator for API routes requiring admin authentication.
    Returns JSON error if not authenticated.
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


def format_dish_for_response(dish):
    """
    Formats a dish document for API response
    """
    return {
        "_id": str(dish["_id"]),
        "name": dish.get("name", ""),
        "price": float(dish.get("price", 0)),
        "category": dish.get("category"),
        "image_url": dish.get("image_url", ""),
        "description": dish.get("description", ""),
        "available": bool(dish.get("available", True)),
        "is_active": bool(dish.get("is_active", True)),
        "created_at": dish.get("created_at"),
        "updated_at": dish.get("updated_at")
    }


# =========================
# PUBLIC API - GET ALL DISHES
# =========================

@dishes_bp.route("/", methods=["GET"])
def get_dishes():
    """
    PUBLIC API: Returns all active dishes for users.
    NO AUTHENTICATION REQUIRED

    Response format:
    {
        "success": true,
        "dishes": [...],
        "count": number
    }
    """
    try:
        if dishes_collection is None:
            return jsonify({"success": False, "error": "Database not available"}), 500

        # Build query for active dishes only
        query = {"is_active": True}

        dishes = list(dishes_collection.find(query))

        # Format dishes for frontend
        formatted_dishes = [format_dish_for_response(dish) for dish in dishes]

        return jsonify({
            "success": True,
            "dishes": formatted_dishes,
            "count": len(formatted_dishes)
        })

    except Exception as e:
        print(f"Error in get_dishes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@dishes_bp.route("/categories", methods=["GET"])
def get_categories():
    if categories_collection is None:
        return jsonify({"error": "Database not available"}), 500
    categories = list(categories_collection.find({"is_active": True}))
    return jsonify([
        {
            "id": str(c["_id"]),
            "name": c["name"],
            "slug": c["slug"]
        } for c in categories
    ])
@dishes_bp.route("/categories", methods=["POST"])
@admin_required
def add_category():
    name = request.json.get("name")
    slug = name.lower().replace(" ", "-")

    if categories_collection.find_one({"slug": slug}):
        return jsonify({"error": "Category already exists"}), 400

    categories_collection.insert_one({
        "name": name,
        "slug": slug,
        "is_active": True,
        "created_at": datetime.utcnow()
    })

    return jsonify({"success": True})

# =========================
# PUBLIC API - GET SINGLE DISH
# =========================

@dishes_bp.route("/signature", methods=["GET"])
def get_signature_dishes():
    """
    PUBLIC API: Returns only signature dishes for landing page.
    NO AUTHENTICATION REQUIRED

    Response format:
    {
        "success": true,
        "dishes": [...],
        "count": number
    }
    """
    try:
        if dishes_collection is None:
            return jsonify({"success": False, "error": "Database not available"}), 500

        # Build query for active signature dishes only
        query = {"is_active": True, "is_signature": True}

        dishes = list(dishes_collection.find(query))

        # Format dishes for frontend
        formatted_dishes = [format_dish_for_response(dish) for dish in dishes]

        return jsonify({
            "success": True,
            "dishes": formatted_dishes,
            "count": len(formatted_dishes)
        })

    except Exception as e:
        print(f"Error in get_signature_dishes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@dishes_bp.route("/<dish_id>", methods=["GET"])
def get_dish(dish_id):
    """
    PUBLIC API: Returns details of a single dish.
    """
    try:
        dish = dishes_collection.find_one({"_id": ObjectId(dish_id)})

        if not dish:
            return jsonify({"success": False, "error": "Dish not found"}), 404

        formatted_dish = format_dish_for_response(dish)

        return jsonify({
            "success": True,
            "dish": formatted_dish
        })
    except Exception as e:
        print(f"Error in get_dish: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
