import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

load_dotenv()

def send_pdf_via_email(customer_email, customer_name, pdf_buffer, booking_id):
    """
    Send PDF via Gmail SMTP
    """
    try:
        sender_email = os.getenv("EMAIL_USER")  # Your personal Gmail from .env
        sender_password = os.getenv("EMAIL_PASSWORD")  # App password from .env
        

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = customer_email
        msg['Subject'] = f"Order Confirmation & Ingredients List - Booking {booking_id[:8]}"
        
        body = f"""
Dear {customer_name},

Thank you for choosing Omsgr Caterings!

Please find attached your complete order summary and ingredients list.

Order Details:
- Booking ID: {booking_id[:8]}
- Document: Complete ingredients list with categorization
- Pricing: Full breakdown included in PDF

If you have any questions, feel free to contact us.

Best regards,
Omsgr Caterings Team

---
This is an automated email. Please do not reply to this address.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        pdf_buffer.seek(0)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_buffer.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename=order_{booking_id[:8]}.pdf')
        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, customer_email, text)
        server.quit()
        
        return True

    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False


def send_booking_confirmation(customer_email, customer_name, booking_details):
    """
    Send booking confirmation email to customer
    """
    try:
        sender_email = os.getenv("EMAIL_USER")  # Your personal Gmail from .env
        sender_password = os.getenv("EMAIL_PASSWORD")  # App password from .env

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = customer_email
        msg['Subject'] = f"Booking Confirmation - {booking_details.get('booking_id', '')[:8]}"

        body = f"""
Dear {customer_name},

Thank you for choosing Omsgr Caterings!

Your booking has been confirmed successfully.

Booking Details:
- Booking ID: {booking_details.get('booking_id', '')[:8]}
- Event Date: {booking_details.get('event_date', '')}
- Time Slot: {booking_details.get('time_slot', '')}
- Service Type: {booking_details.get('service_type', '')}
- Guests: {booking_details.get('guests', '')}
- Location: {booking_details.get('event_location', '')}

We will contact you soon with further details and the ingredients list.

Best regards,
Omsgr Caterings Team

---
This is an automated email. Please do not reply to this address.
        """

        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, customer_email, text)
        server.quit()

        return True

    except Exception as e:
        print(f"Booking confirmation email failed: {str(e)}")
        return False


def send_ingredients_list(customer_email, customer_name, booking_details, ingredients_list):
    """
    Send ingredients list email to customer
    """
    try:
        sender_email = os.getenv("EMAIL_USER")  # Your personal Gmail from .env
        sender_password = os.getenv("EMAIL_PASSWORD")  # App password from .env

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = customer_email
        msg['Subject'] = f"Ingredients List - Booking {booking_details.get('booking_id', '')[:8]}"

        # Format ingredients list
        ingredients_text = "\n".join([f"- {item}" for item in ingredients_list]) if ingredients_list else "Ingredients list will be provided soon."

        body = f"""
Dear {customer_name},

Here is your complete ingredients list for the upcoming event.

Booking Details:
- Booking ID: {booking_details.get('booking_id', '')[:8]}
- Event Date: {booking_details.get('event_date', '')}
- Time Slot: {booking_details.get('time_slot', '')}
- Guests: {booking_details.get('guests', '')}

Ingredients List:
{ingredients_text}

Please ensure all ingredients are fresh and ready for preparation.

If you have any questions, feel free to contact us.

Best regards,
Omsgr Caterings Team

---
This is an automated email. Please do not reply to this address.
        """

        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, customer_email, text)
        server.quit()

        return True

    except Exception as e:
        print(f"Ingredients list email failed: {str(e)}")
        return False


def send_admin_notification(booking_details):
    """
    Send notification to admin about new booking
    """
    try:
        sender_email = os.getenv("EMAIL_USER")  # Your personal Gmail from .env
        sender_password = os.getenv("EMAIL_PASSWORD")  # App password from .env
        admin_email = os.getenv("ADMIN_EMAIL")  # Admin email from .env

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = admin_email
        msg['Subject'] = f"New Booking Alert - {booking_details.get('booking_id', '')[:8]}"

        body = f"""
New Booking Received!

Customer Details:
- Name: {booking_details.get('customer_name', '')}
- Email: {booking_details.get('email', '')}
- Mobile: {booking_details.get('mobile', '')}

Booking Details:
- Booking ID: {booking_details.get('booking_id', '')[:8]}
- Event Date: {booking_details.get('event_date', '')}
- Time Slot: {booking_details.get('time_slot', '')}
- Service Type: {booking_details.get('service_type', '')}
- Guests: {booking_details.get('guests', '')}
- Location: {booking_details.get('event_location', '')}

Please review and confirm the booking.

Best regards,
Catering Services System

---
This is an automated notification.
        """

        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, admin_email, text)
        server.quit()

        return True

    except Exception as e:
        print(f"Admin notification email failed: {str(e)}")
        return False
