from flask import current_app


def send_whatsapp_message(phone_number, message):
    """
    MANUAL WhatsApp sending helper.
    Prints message for copy–paste into WhatsApp.
    """

    try:
        print("📱 WhatsApp Message (Manual Copy)")
        print(f"To: {phone_number}")
        print("-" * 50)
        print(message)
        print("-" * 50)
        return True

    except Exception as e:
        print(f"❌ WhatsApp message generation failed: {e}")
        return False


def send_booking_confirmation_whatsapp(phone_number, customer_name, booking_details):
    """
    Generates booking confirmation WhatsApp message.
    """

    website_url = current_app.config.get('WEBSITE_URL', 'https://chetan-catering-services.onrender.com')
    rating_url = current_app.config.get('RATING_URL', f'{website_url}/rating')

    message = f"""
Booking Confirmation – Omsgr Catering Services

Dear {customer_name},

Thank you for your booking. We are pleased to confirm the following details:

Event Date: {booking_details.get('event_date')}
Time Slot: {booking_details.get('time_slot')}
Guests: {booking_details.get('guests')}
Service Type: {booking_details.get('service_type')}

Total Amount: ₹{booking_details.get('pricing', {}).get('total')}

The ingredients list will be shared with you via email within 24 hours.

For any queries, please contact us.
Phone: +91 733 822 1281

Visit our website: {website_url}

We would love your feedback! Please rate our service here: {rating_url}

Thank you for choosing Omsgr Caterings.
"""

    return send_whatsapp_message(phone_number, message)


def send_ingredients_whatsapp(phone_number, customer_name, booking_details, ingredients_list):
    """
    Generates ingredients list WhatsApp message.
    """

    website_url = current_app.config.get('WEBSITE_URL', 'https://chetan-catering-services.onrender.com')
    rating_url = current_app.config.get('RATING_URL', f'{website_url}/rating')

    if isinstance(ingredients_list, list):
        ingredients_text = "\n".join([f"- {item}" for item in ingredients_list])
    else:
        ingredients_text = ingredients_list

    message = f"""
Ingredients List – Omsgr Caterings

Dear {customer_name},

Please find below the ingredients required for your event:

Event Date: {booking_details.get('event_date')}
Time Slot: {booking_details.get('time_slot')}
Guests: {booking_details.get('guests')}

Required Ingredients:
{ingredients_text}

Kindly ensure these items are available at the venue.

For assistance, please contact us.
Phone: +91 733 822 1281

Visit our website: {website_url}

We would appreciate your feedback! Give us a rating here: {rating_url}

Regards,
Omsgr Caterings
"""

    return send_whatsapp_message(phone_number, message)


def send_ingredients_pdf_ready_whatsapp(phone_number, customer_name, booking_details):
    """
    Generates WhatsApp message notifying the customer that
    the final ingredients PDF has been sent via email.
    No direct PDF link is included.
    """

    website_url = current_app.config.get('WEBSITE_URL', 'https://chetan-catering-services.onrender.com')
    rating_url = current_app.config.get('RATING_URL', f'{website_url}/rating')

    booking_id = booking_details.get('booking_id') or booking_details.get('_id', 'N/A')
    booking_id_display = (
        booking_id[:12] if isinstance(booking_id, str) and len(booking_id) > 12 else str(booking_id)
    )

    booking_date = booking_details.get('booking_date', 'N/A')

    message = f"""Hello {customer_name},

Your final ingredients list is ready.

Booking ID: {booking_id_display}
Booking Date: {booking_date}
Event Date: {booking_details.get('event_date', 'N/A')}
Time Slot: {booking_details.get('time_slot', 'N/A')}
Guests: {booking_details.get('guests', 'N/A')}

The complete ingredients PDF has been sent to your registered email address.
(Please check your Inbox or Spam folder)

For any assistance, please contact us.
Phone: +91 733 822 1281

Visit our website: {website_url}

We value your opinion! Please give us a rating here: {rating_url}
"""

    return send_whatsapp_message(phone_number, message)
