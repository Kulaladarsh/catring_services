from flask import Blueprint, request, jsonify, session
from backend.db import ingredients_collection, orders_collection, final_ingredients_collection, dishes_collection
from functools import wraps
from bson import ObjectId
from datetime import datetime
from collections import defaultdict

ingredients_bp = Blueprint("ingredients", __name__, url_prefix="/admin/api/ingredients")

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
# INGREDIENT DATABASE (DISH → INGREDIENTS MAPPING)
# =========================

# Ingredients are now stored dynamically in MongoDB dishes collection


# =========================
# HELPER FUNCTIONS
# =========================







# =========================
# API ROUTES
# =========================




@ingredients_bp.route("/", methods=["GET"])
@admin_required
def get_ingredients():
    """
    Get all ingredients from the database
    """
    try:
        ingredients = list(ingredients_collection.find({}))
        
        formatted = []
        for ing in ingredients:
            formatted.append({
                "_id": str(ing["_id"]),
                "name": ing.get("name", ""),
                "quantity": ing.get("quantity", 0),
                "unit": ing.get("unit", ""),
                "checked": ing.get("checked", False)
            })
        
        return jsonify({
            "success": True,
            "ingredients": formatted,
            "count": len(formatted)
        })
        
    except Exception as e:
        print(f"Error fetching ingredients: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/<ingredient_id>", methods=["PATCH"])
@admin_required
def update_ingredient(ingredient_id):
    """
    Update an ingredient (quantity, checked status)
    
    Request body:
    {
        "quantity": 100 (optional),
        "checked": true (optional)
    }
    """
    try:
        data = request.get_json() or {}
        
        update_data = {"updated_at": datetime.utcnow()}
        
        if "quantity" in data:
            update_data["quantity"] = float(data["quantity"])
        
        if "checked" in data:
            update_data["checked"] = bool(data["checked"])
        
        result = ingredients_collection.update_one(
            {"_id": ObjectId(ingredient_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({
                "success": True,
                "message": "Ingredient updated successfully"
            })
        else:
            return jsonify({
                "success": True,
                "message": "No changes made"
            })
        
    except Exception as e:
        print(f"Error updating ingredient: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/bulk-update", methods=["POST"])
@admin_required
def bulk_update_ingredients():
    """
    Bulk update multiple ingredients
    
    Request body:
    {
        "updates": [
            {"_id": "id1", "quantity": 100, "checked": true},
            {"_id": "id2", "checked": false}
        ]
    }
    """
    try:
        data = request.get_json() or {}
        updates = data.get("updates", [])
        
        updated_count = 0
        for update in updates:
            ingredient_id = update.get("_id")
            if not ingredient_id:
                continue
            
            update_data = {"updated_at": datetime.utcnow()}
            
            if "quantity" in update:
                update_data["quantity"] = float(update["quantity"])
            
            if "checked" in update:
                update_data["checked"] = bool(update["checked"])
            
            result = ingredients_collection.update_one(
                {"_id": ObjectId(ingredient_id)},
                {"$set": update_data}
            )
            
            updated_count += result.modified_count
        
        return jsonify({
            "success": True,
            "message": f"Updated {updated_count} ingredients",
            "count": updated_count
        })
        
    except Exception as e:
        print(f"Error bulk updating ingredients: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/clear", methods=["DELETE"])
@admin_required
def clear_ingredients():
    """
    Clear all ingredients from the database
    """
    try:
        result = ingredients_collection.delete_many({})

        return jsonify({
            "success": True,
            "message": f"Cleared {result.deleted_count} ingredients",
            "count": result.deleted_count
        })

    except Exception as e:
        print(f"Error clearing ingredients: {str(e)}")
        return jsonify({"error": str(e)}), 500


# =========================
# FINAL INGREDIENTS MANAGEMENT (PER BOOKING)
# =========================

def get_dish_ingredients_from_db(dish_name):
    """
    Get ingredients for a dish from the dishes collection (new schema)
    """
    dish = dishes_collection.find_one({"name": {"$regex": f"^{dish_name}$", "$options": "i"}})
    if dish and dish.get("ingredients"):
        return dish["ingredients"]
    # Return empty list if no ingredients found
    return []


def generate_final_ingredients(booking_id):
    """
    Auto-generate final ingredients for a booking based on dish templates
    Uses the formula: final_quantity = (base_quantity_for_10 / 10) × number_of_guests
    """
    # Get booking details
    booking = orders_collection.find_one({"_id": ObjectId(booking_id)})
    if not booking:
        return None

    guests = booking.get("guests", 1)
    dishes = booking.get("dishes", [])

    # Define valid unit types to preserve original units
    VALID_UNITS = {
        "gm", "kg", "ml", "litre", "liter", "cup", "cups", "tbsp", "tsp",
        "piece", "pieces", "packet", "packets", "bunch", "bunches",
        "dozen", "slice", "slices", "can", "cans", "bottle", "bottles"
    }

    # Aggregate ingredients by category
    ingredient_totals = defaultdict(lambda: {"quantity": 0, "unit": None, "category": None})

    for dish_item in dishes:
        dish_name = dish_item.get("dish_name", "")
        quantity = dish_item.get("quantity", 1)

        # Get ingredients from dish database
        ingredients = get_dish_ingredients_from_db(dish_name)

        for ing in ingredients:
            ing_name = ing["name"]
            # Base quantity is for 10 persons, so divide by 10 and multiply by guests
            base_qty_for_10 = ing.get("quantity_per_plate", ing.get("per_plate", 0))
            ing_unit = ing.get("unit", "").lower().strip()

            # Preserve original unit if it's valid, otherwise try to infer from name
            if ing_unit in VALID_UNITS:
                final_unit = ing_unit
            elif "milk" in ing_name.lower():
                final_unit = "litre"
            elif any(word in ing_name.lower() for word in ["oil", "ghee", "butter"]):
                final_unit = "ml"
            elif any(word in ing_name.lower() for word in ["rice", "flour", "sugar", "salt"]):
                final_unit = "kg"
            elif any(word in ing_name.lower() for word in ["onion", "potato", "tomato", "vegetable"]):
                final_unit = "kg"
            elif any(word in ing_name.lower() for word in ["cumin", "turmeric", "chili", "coriander"]):
                final_unit = "gm"
            else:
                final_unit = "gm"  # Default fallback

            # Determine category based on ingredient name
            ing_category = ing.get("category", "")
            if not ing_category:
                ing_name_lower = ing_name.lower()
                if any(word in ing_name_lower for word in ["chicken", "mutton", "fish", "egg", "meat"]):
                    ing_category = "Non-Vegetarian"
                elif any(word in ing_name_lower for word in ["onion", "potato", "tomato", "carrot", "beans", "peas", "vegetable"]):
                    ing_category = "Vegetables"
                elif any(word in ing_name_lower for word in ["cumin", "turmeric", "chili", "coriander", "garam", "masala", "spices"]):
                    ing_category = "Spices"
                else:
                    ing_category = "Others"

            # Scaling formula: (base_quantity_for_10 / 10) × number_of_guests × dish_quantity
            # This preserves the unit type (kg stays kg, litre stays litre, etc.)
            scaled_qty = (base_qty_for_10 / 10) * guests * quantity

            # Aggregate by ingredient name
            if ing_name in ingredient_totals:
                ingredient_totals[ing_name]["quantity"] += scaled_qty
            else:
                ingredient_totals[ing_name]["quantity"] = scaled_qty
                ingredient_totals[ing_name]["unit"] = final_unit
                ingredient_totals[ing_name]["category"] = ing_category

    # Convert to list format with categories
    final_ingredients = []
    for ing_name, data in ingredient_totals.items():
        final_ingredients.append({
            "name": ing_name,
            "quantity": round(data["quantity"], 2),
            "unit": data["unit"],  # Preserve original unit
            "category": data["category"],
            "checked": True  # Default to checked
        })

    # Sort by category order: Vegetables, Non-Vegetarian, Spices, Others
    category_order = {"Vegetables": 0, "Non-Vegetarian": 1, "Spices": 2, "Others": 3}
    final_ingredients.sort(key=lambda x: category_order.get(x["category"], 4))

    return final_ingredients


@ingredients_bp.route("/booking/<booking_id>/generate", methods=["POST"])
@admin_required
def generate_booking_ingredients(booking_id):
    """
    Auto-generate final ingredients for a specific booking
    """
    try:
        # Check if final ingredients already exist
        existing = final_ingredients_collection.find_one({"booking_id": booking_id})
        if existing:
            return jsonify({
                "success": False,
                "error": "Final ingredients already exist for this booking"
            }), 400

        # Generate ingredients
        final_ingredients = generate_final_ingredients(booking_id)
        if final_ingredients is None:
            return jsonify({"error": "Booking not found"}), 404

        # Save to final_ingredients collection
        doc = {
            "booking_id": booking_id,
            "ingredients": final_ingredients,
            "approved_by_admin": False,
            "approved_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = final_ingredients_collection.insert_one(doc)

        return jsonify({
            "success": True,
            "message": "Final ingredients generated successfully",
            "ingredients": final_ingredients,
            "count": len(final_ingredients)
        })

    except Exception as e:
        print(f"Error generating booking ingredients: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/booking/<booking_id>", methods=["GET"])
@admin_required
def get_booking_final_ingredients(booking_id):
    """
    Get final ingredients for a specific booking
    """
    try:
        final_ingredients = final_ingredients_collection.find_one({"booking_id": booking_id})

        if not final_ingredients:
            return jsonify({
                "success": False,
                "error": "Final ingredients not found for this booking"
            }), 404

        return jsonify({
            "success": True,
            "booking_id": booking_id,
            "ingredients": final_ingredients.get("ingredients", []),
            "approved_by_admin": final_ingredients.get("approved_by_admin", False),
            "approved_at": final_ingredients.get("approved_at"),
            "count": len(final_ingredients.get("ingredients", []))
        })

    except Exception as e:
        print(f"Error fetching booking final ingredients: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/booking/<booking_id>", methods=["PUT"])
@admin_required
def update_booking_final_ingredients(booking_id):
    """
    Update final ingredients for a specific booking (add, edit, remove)

    Request body:
    {
        "ingredients": [
            {"name": "Rice", "quantity": 500, "unit": "g", "checked": true},
            ...
        ]
    }
    """
    try:
        data = request.get_json() or {}
        ingredients = data.get("ingredients", [])

        # Validate ingredients
        for ing in ingredients:
            if not ing.get("name"):
                return jsonify({"error": "All ingredients must have a name"}), 400

        # Update final ingredients
        result = final_ingredients_collection.update_one(
            {"booking_id": booking_id},
            {
                "$set": {
                    "ingredients": ingredients,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({"error": "Final ingredients not found for this booking"}), 404

        return jsonify({
            "success": True,
            "message": "Final ingredients updated successfully",
            "count": len(ingredients)
        })

    except Exception as e:
        print(f"Error updating booking final ingredients: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/booking/<booking_id>/approve", methods=["POST"])
@admin_required
def approve_booking_final_ingredients(booking_id):
    """
    Approve final ingredients for a booking (admin approval)
    """
    try:
        username = session.get("admin_username", "admin")

        result = final_ingredients_collection.update_one(
            {"booking_id": booking_id},
            {
                "$set": {
                    "approved_by_admin": True,
                    "approved_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({"error": "Final ingredients not found for this booking"}), 404

        # Mark ingredients as sent in booking and update order status to APPROVED
        from backend.models import mark_ingredients_sent, update_booking_status
        mark_ingredients_sent(booking_id)
        update_booking_status(booking_id, "APPROVED")

        return jsonify({
            "success": True,
            "message": "Final ingredients approved successfully and order status updated to APPROVED",
            "approved_by": username,
            "approved_at": datetime.utcnow().isoformat()
        })

    except Exception as e:
        print(f"Error approving booking final ingredients: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/booking/<booking_id>/regenerate", methods=["POST"])
@admin_required
def regenerate_booking_ingredients(booking_id):
    """
    Regenerate final ingredients for a booking after dish changes
    This handles cascade delete when dishes are removed
    """
    try:
        # Check if final ingredients exist
        existing = final_ingredients_collection.find_one({"booking_id": booking_id})
        if not existing:
            return jsonify({"error": "Final ingredients not found for this booking"}), 404

        # Generate fresh ingredients
        final_ingredients = generate_final_ingredients(booking_id)
        if final_ingredients is None:
            return jsonify({"error": "Booking not found"}), 404

        # Update final ingredients
        result = final_ingredients_collection.update_one(
            {"booking_id": booking_id},
            {
                "$set": {
                    "ingredients": final_ingredients,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return jsonify({
            "success": True,
            "message": "Final ingredients regenerated successfully",
            "ingredients": final_ingredients,
            "count": len(final_ingredients)
        })

    except Exception as e:
        print(f"Error regenerating booking ingredients: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/booking/<booking_id>/remove-dish/<dish_name>", methods=["DELETE"])
@admin_required
def remove_dish_from_booking(booking_id, dish_name):
    """
    Remove a specific dish from a booking and regenerate final ingredients
    """
    try:
        # Get the booking
        booking = orders_collection.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # Remove the dish from the booking's dish list
        result = orders_collection.update_one(
            {"_id": ObjectId(booking_id)},
            {"$pull": {"dishes": {"dish_name": {"$regex": f"^{dish_name}$", "$options": "i"}}}}
        )

        if result.modified_count > 0:
            # Regenerate final ingredients
            final_ingredients = generate_final_ingredients(booking_id)
            if final_ingredients is not None:
                final_ingredients_collection.update_one(
                    {"booking_id": booking_id},
                    {
                        "$set": {
                            "ingredients": final_ingredients,
                            "updated_at": datetime.utcnow()
                        }
                    },
                    upsert=True
                )

            return jsonify({
                "success": True,
                "message": f"Dish '{dish_name}' removed from booking and ingredients regenerated",
                "ingredients": final_ingredients,
                "count": len(final_ingredients) if final_ingredients else 0
            })
        else:
            return jsonify({"error": "Dish not found in booking"}), 404

    except Exception as e:
        print(f"Error removing dish from booking: {str(e)}")
        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/booking/<booking_id>/pdf", methods=["GET"])
@admin_required
def generate_booking_pdf(booking_id):
    """
    ✅ UPDATED: Generate PDF using new comprehensive generator
    """
    try:
        # Get booking details
        booking = orders_collection.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # Get final ingredients
        final_ingredients = final_ingredients_collection.find_one({"booking_id": booking_id})
        if not final_ingredients or not final_ingredients.get("approved_by_admin"):
            return jsonify({"error": "Final ingredients not approved yet"}), 400

        # Convert ObjectId to string for PDF generation
        booking['_id'] = str(booking['_id'])
        
        # Generate PDF with NEW comprehensive function
        from backend.utils.pdf_generator import generate_ingredients_pdf
        pdf_buffer = generate_ingredients_pdf(booking, final_ingredients.get("ingredients", []))

        from flask import send_file
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"order_{booking_id[:8]}.pdf",
            mimetype='application/pdf'
        )


    except Exception as e:

        print(f"Error generating booking PDF: {str(e)}")

        return jsonify({"error": str(e)}), 500


@ingredients_bp.route("/booking/<booking_id>/share", methods=["POST"])

@admin_required

def share_booking_pdf(booking_id):

    """

    ✅ NEW: Share PDF via Email & WhatsApp

    """

    try:

        data = request.get_json() or {}

        share_method = data.get("method", "both")  # email, whatsapp, or both

        

        # Get booking details

        booking = orders_collection.find_one({"_id": ObjectId(booking_id)})

        if not booking:

            return jsonify({"error": "Booking not found"}), 404

        

        # Get final ingredients

        final_ingredients = final_ingredients_collection.find_one({"booking_id": booking_id})

        if not final_ingredients or not final_ingredients.get("approved_by_admin"):

            return jsonify({"error": "Final ingredients not approved yet"}), 400

        

        # Generate PDF

        from backend.utils.pdf_generator import generate_ingredients_pdf

        booking['_id'] = str(booking['_id'])

        pdf_buffer = generate_ingredients_pdf(booking, final_ingredients.get("ingredients", []))

        

        results = {

            "email_sent": False,

            "whatsapp_link": None

        }

        

        # Send via Email

        if share_method in ["email", "both"]:

            from backend.utils.email import send_pdf_via_email

            email_sent = send_pdf_via_email(

                customer_email=booking.get("email"),

                customer_name=booking.get("customer_name"),

                pdf_buffer=pdf_buffer,

                booking_id=booking_id

            )

            results["email_sent"] = email_sent

        

        # Send via WhatsApp

        if share_method in ["whatsapp", "both"]:

            from backend.utils.whatsapp import send_pdf_via_whatsapp

            # Generate public PDF URL (you'll need to host PDF temporarily)

            pdf_url = f"https://yourdomain.com/api/pdf/{booking_id}"  # Replace with actual URL

            

            whatsapp_link = send_pdf_via_whatsapp(

                phone_number=booking.get("mobile"),

                customer_name=booking.get("customer_name"),

                booking_id=booking_id,

                pdf_url=pdf_url

            )

            results["whatsapp_link"] = whatsapp_link

        

        return jsonify({

            "success": True,

            "message": "PDF sharing initiated",

            **results

        })

        

    except Exception as e:

        print(f"Error sharing PDF: {str(e)}")

        return jsonify({"error": str(e)}), 500

