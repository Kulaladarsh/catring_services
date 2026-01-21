def to_base_unit(value, unit):
    """
    Convert any unit to base units (grams for weight, milliliters for liquid).
    For non-convertible units like pieces, packets, etc., keep as is.
    Always calculate in base units internally.

    Args:
        value (float): The quantity value
        unit (str): The unit string (case-insensitive)

    Returns:
        tuple: (converted_value, base_unit)

    Raises:
        ValueError: If unit is invalid
    """
    unit = unit.lower().strip()

    # Weight units
    if unit in ["kg", "kilogram", "kilograms"]:
        return value * 1000, "g"
    if unit in ["g", "gm", "gram", "grams"]:
        return value, "g"
    if unit in ["oz", "ounce", "ounces"]:
        return value * 28.35, "g"
    if unit in ["lb", "pound", "pounds"]:
        return value * 453.59, "g"
    if unit in ["mg", "milligram", "milligrams"]:
        return value / 1000, "g"

    # Volume units
    if unit in ["l", "ltr", "liter", "liters", "litre", "litres"]:
        return value * 1000, "ml"
    if unit in ["ml", "milliliter", "milliliters", "millilitre", "millilitres"]:
        return value, "ml"

    # Count units (non-convertible)
    if unit in ["piece", "pieces", "pcs", "pc"]:
        return value, "pcs"
    if unit in ["packet", "packets", "pkt"]:
        return value, "pkt"
    if unit in ["bunch", "bunches"]:
        return value, "bunch"
    if unit in ["dozen", "dozens"]:
        return value, "dozen"
    if unit in ["slice", "slices"]:
        return value, "slice"
    if unit in ["can", "cans"]:
        return value, "can"
    if unit in ["bottle", "bottles"]:
        return value, "bottle"
    if unit in ["cup", "cups"]:
        return value, "cup"
    if unit in ["tbsp", "tablespoon", "tablespoons"]:
        return value, "tbsp"
    if unit in ["tsp", "teaspoon", "teaspoons"]:
        return value, "tsp"

    raise ValueError(f"Invalid unit: {unit}")


def to_display_unit(value, base_unit):
    """
    Convert base unit values back to appropriate display units.
    Only convert when displaying (UI / PDF).

    Args:
        value (float): The value in base units
        base_unit (str): The base unit ("g" or "ml")

    Returns:
        tuple: (display_value, display_unit)
    """
    if base_unit == "g":
        if value >= 1000:
            return round(value / 1000, 2), "kg"
        return round(value, 2), "g"

    if base_unit == "ml":
        if value >= 1000:
            return round(value / 1000, 2), "ltr"
        return round(value, 2), "ml"

    return value, base_unit
