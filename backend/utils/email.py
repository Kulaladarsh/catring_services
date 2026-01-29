import os
import logging
import threading
import base64
from io import BytesIO
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, To, From
from email_validator import validate_email, EmailNotValidError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_not_exception_type

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
MAIL_DEFAULT_SENDER = "kulaladarsh1@gmail.com"
MAIL_USERNAME = "kulaladarsh1@gmail.com"
ADMIN_EMAIL = "kulaladarsh1@gmail.com"  # Use the same personal email used for PDF sharing

def validate_email_address(email):
    """Validate email address format and deliverability."""
    try:
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError as e:
        logger.error(f"Invalid email address: {email} - {str(e)}")
        return None

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_not_exception_type(ValueError)
)
def send_email_via_sendgrid(to_email, subject, html_content, plain_content=None, attachments=None):
    """Send email using SendGrid API with retry logic."""
    if not SENDGRID_API_KEY:
        raise ValueError("SENDGRID_API_KEY environment variable not set")

    # Validate recipient email
    validated_email = validate_email_address(to_email)
    if not validated_email:
        raise ValueError(f"Invalid recipient email: {to_email}")

    message = Mail(
        from_email=From(MAIL_DEFAULT_SENDER, "OMSGr Caterings"),
        to_emails=To(validated_email),
        subject=subject,
        html_content=html_content
    )

    # Add plain text content if provided
    if plain_content:
        from sendgrid.helpers.mail import PlainTextContent
        message.plain_text_content = PlainTextContent(plain_content)

    # Add attachments if provided
    if attachments:
        for attachment in attachments:
            sg_attachment = Attachment(
                file_content=FileContent(base64.b64encode(attachment['data']).decode()),
                file_name=FileName(attachment['filename']),
                file_type=FileType(attachment['type']),
                disposition=Disposition('attachment')
            )
            message.attachment = sg_attachment

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Email sent successfully to {validated_email}. Status: {response.status_code}")
        return {'success': True, 'status_code': response.status_code}
    except Exception as e:
        logger.error(f"Failed to send email to {validated_email}: {str(e)}")
        raise

def send_email_async(to_email, subject, html_content, plain_content=None, attachments=None):
    """Send email asynchronously to prevent blocking."""
    def send():
        try:
            send_email_via_sendgrid(to_email, subject, html_content, plain_content, attachments)
        except Exception as e:
            logger.error(f"Async email sending failed: {str(e)}")

    thread = threading.Thread(target=send)
    thread.daemon = True
    thread.start()


# =========================
# 1. BOOKING CONFIRMATION EMAIL (TEXT/HTML ONLY - NO PDF)
# =========================

def send_booking_confirmation(customer_email, customer_name, booking_details):
    """
    Send booking confirmation email to customer (TEXT/HTML ONLY - NO PDF).
    This is sent immediately after booking is completed.
    
    Args:
        customer_email: Customer's email address
        customer_name: Customer's name
        booking_details: Dictionary with booking information
    
    Returns:
        dict: {'success': True/False, 'message': string}
    """
    try:
        validated_email = validate_email_address(customer_email)
        if not validated_email:
            return {'success': False, 'error': 'Invalid email address'}

        booking_id = booking_details.get('booking_id', booking_details.get('_id', 'N/A'))
        if isinstance(booking_id, str) and len(booking_id) > 12:
            booking_id_display = booking_id[:12]
        else:
            booking_id_display = str(booking_id)

        subject = f"🎉 Booking Confirmed - OMSGr Caterings"

        # Get pricing details
        pricing = booking_details.get('pricing', {})
        total_amount = pricing.get('total', 0)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #EA580C 0%, #DC2626 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e5e5; }}
                .details {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .details table {{ width: 100%; }}
                .details td {{ padding: 8px; border-bottom: 1px solid #dee2e6; }}
                .details td:first-child {{ font-weight: bold; color: #495057; width: 40%; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; 
                          border-radius: 0 0 10px 10px; font-size: 12px; color: #6c757d; }}
                .highlight {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; 
                            margin: 20px 0; border-radius: 4px; }}
                .btn {{ background: #EA580C; color: white; padding: 12px 30px; text-decoration: none; 
                       border-radius: 6px; display: inline-block; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 28px;">🍽️ OMSGr Caterings</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your Booking is Confirmed!</p>
                </div>
                
                <div class="content">
                    <h2 style="color: #EA580C; margin-top: 0;">Dear {customer_name},</h2>
                    <p>Thank you for choosing OMSGr Caterings! We're excited to serve you.</p>
                    <p>Your booking has been <strong>successfully confirmed</strong>. We've received all your details and will start preparing for your event.</p>
                    
                    <div class="details">
                        <h3 style="margin-top: 0; color: #495057;">📋 Booking Details</h3>
                        <table>
                            <tr>
                                <td>Booking ID:</td>
                                <td><strong>{booking_id_display}</strong></td>
                            </tr>
                            <tr>
                                <td>Event Date:</td>
                                <td>{booking_details.get('event_date', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Time Slot:</td>
                                <td>{booking_details.get('time_slot', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Number of Guests:</td>
                                <td>{booking_details.get('guests', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Service Type:</td>
                                <td>{booking_details.get('service_type', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Food Preference:</td>
                                <td>{booking_details.get('food_preference', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Event Location:</td>
                                <td>{booking_details.get('event_location', 'N/A')}</td>
                            </tr>
                            <tr style="background: #fff3cd;">
                                <td><strong>Total Amount:</strong></td>
                                <td><strong style="font-size: 18px; color: #EA580C;">₹{total_amount:.2f}</strong></td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="highlight">
                        <strong>📝 What's Next?</strong>
                        <p style="margin: 10px 0 0 0;">Our team will review your order and prepare a detailed ingredients list. You'll receive the finalized ingredients list via email within 24-48 hours.</p>
                    </div>
                    
                    <p><strong>Need Help?</strong><br>
                    If you have any questions or need to make changes to your booking, please contact us:</p>
                    <ul style="list-style: none; padding: 0;">
                        <li>📞 Phone: +91-XXXXXXXXXX</li>
                        <li>📧 Email: info@omsgrcaterings.com</li>
                    </ul>
                    
                    <p style="margin-top: 30px;">We look forward to making your event memorable!</p>
                    <p>Warm regards,<br><strong>OMSGr Caterings Team</strong></p>
                </div>
                
                <div class="footer">
                    <p style="margin: 0;">This is an automated confirmation email.</p>
                    <p style="margin: 5px 0 0 0;">© 2024 OMSGr Caterings. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send email WITHOUT PDF attachment
        send_email_async(validated_email, subject, html_content)

        logger.info(f"Booking confirmation email sent to {validated_email} for booking {booking_id_display}")
        return {'success': True, 'message': 'Booking confirmation email queued for sending'}

    except Exception as e:
        logger.error(f"Booking confirmation email failed: {str(e)}")
        return {'success': False, 'error': str(e)}


# =========================
# 2. INGREDIENTS LIST EMAIL (TEXT/HTML ONLY - NO PDF)
# =========================

def send_ingredients_list(customer_email, customer_name, booking_details, ingredients_list):
    """
    Send ingredients list email to customer (TEXT/HTML ONLY - NO PDF).
    This is sent when admin sends ingredients list manually.

    Args:
        customer_email: Customer's email address
        customer_name: Customer's name
        booking_details: Dictionary with booking information
        ingredients_list: String containing the ingredients list

    Returns:
        dict: {'success': True/False, 'message': string}
    """
    try:
        validated_email = validate_email_address(customer_email)
        if not validated_email:
            return {'success': False, 'error': 'Invalid email address'}

        booking_id = booking_details.get('booking_id', booking_details.get('_id', 'N/A'))
        if isinstance(booking_id, str) and len(booking_id) > 12:
            booking_id_display = booking_id[:12]
        else:
            booking_id_display = str(booking_id)

        subject = f"📋 Ingredients List - Booking {booking_id_display}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10B981 0%, #059669 100%);
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e5e5; }}
                .details {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .details table {{ width: 100%; }}
                .details td {{ padding: 8px; border-bottom: 1px solid #dee2e6; }}
                .details td:first-child {{ font-weight: bold; color: #495057; width: 40%; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center;
                          border-radius: 0 0 10px 10px; font-size: 12px; color: #6c757d; }}
                .ingredients {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;
                               border-left: 4px solid #10B981; }}
                .ingredients pre {{ white-space: pre-wrap; font-family: monospace; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 28px;">🍽️ OMSGr Caterings</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your Ingredients List</p>
                </div>

                <div class="content">
                    <h2 style="color: #10B981; margin-top: 0;">Dear {customer_name},</h2>
                    <p>Here is your ingredients list for the upcoming event.</p>

                    <div class="details">
                        <h3 style="margin-top: 0; color: #495057;">📋 Event Details</h3>
                        <table>
                            <tr>
                                <td>Booking ID:</td>
                                <td><strong>{booking_id_display}</strong></td>
                            </tr>
                            <tr>
                                <td>Event Date:</td>
                                <td>{booking_details.get('event_date', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Time Slot:</td>
                                <td>{booking_details.get('time_slot', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Number of Guests:</td>
                                <td>{booking_details.get('guests', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Event Location:</td>
                                <td>{booking_details.get('event_location', 'N/A')}</td>
                            </tr>
                        </table>
                    </div>

                    <div class="ingredients">
                        <h3 style="margin-top: 0; color: #059669;">🛒 Ingredients List</h3>
                        <pre>{ingredients_list}</pre>
                    </div>

                    <p><strong>Important Instructions:</strong></p>
                    <ul style="list-style: none; padding: 0;">
                        <li>✅ Ensure all ingredients are fresh and of good quality</li>
                        <li>✅ Keep all items ready at the venue before our team arrives</li>
                        <li>✅ Store perishable items properly until the event</li>
                        <li>📞 Contact us immediately if you have any questions</li>
                    </ul>

                    <p><strong>Need Help?</strong><br>
                    If you have any questions about the ingredients list:</p>
                    <ul style="list-style: none; padding: 0;">
                        <li>📞 Phone: +91-XXXXXXXXXX</li>
                        <li>📧 Email: info@omsgrcaterings.com</li>
                    </ul>

                    <p style="margin-top: 30px;">We're looking forward to making your event a success!</p>
                    <p>Best regards,<br><strong>OMSGr Caterings Team</strong></p>
                </div>

                <div class="footer">
                    <p style="margin: 0;">This email contains important information about your booking.</p>
                    <p style="margin: 5px 0 0 0;">© 2024 OMSGr Caterings. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send email WITHOUT PDF attachment
        send_email_async(validated_email, subject, html_content)

        logger.info(f"Ingredients list email sent to {validated_email} for booking {booking_id_display}")
        return {'success': True, 'message': 'Ingredients list email queued for sending'}

    except Exception as e:
        logger.error(f"Ingredients list email failed: {str(e)}")
        return {'success': False, 'error': str(e)}


# =========================
# 3. INGREDIENTS FINALIZATION EMAIL (WITH PDF ATTACHMENT)
# =========================

def send_ingredients_finalization_email(customer_email, customer_name, booking_details, pdf_buffer):
    """
    Send ingredients finalization email with PDF attachment.
    This is sent AFTER admin finalizes the ingredients.
    
    Args:
        customer_email: Customer's email address
        customer_name: Customer's name
        booking_details: Dictionary with booking information
        pdf_buffer: BytesIO object containing the generated PDF
    
    Returns:
        dict: {'success': True/False, 'message': string}
    """
    try:
        validated_email = validate_email_address(customer_email)
        if not validated_email:
            return {'success': False, 'error': 'Invalid email address'}

        booking_id = booking_details.get('booking_id', booking_details.get('_id', 'N/A'))
        if isinstance(booking_id, str) and len(booking_id) > 12:
            booking_id_display = booking_id[:12]
        else:
            booking_id_display = str(booking_id)

        subject = f"📋 Ingredients List Ready - Booking {booking_id_display}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10B981 0%, #059669 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e5e5; }}
                .details {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .details table {{ width: 100%; }}
                .details td {{ padding: 8px; border-bottom: 1px solid #dee2e6; }}
                .details td:first-child {{ font-weight: bold; color: #495057; width: 40%; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; 
                          border-radius: 0 0 10px 10px; font-size: 12px; color: #6c757d; }}
                .highlight {{ background: #d1fae5; padding: 15px; border-left: 4px solid #10B981; 
                            margin: 20px 0; border-radius: 4px; }}
                .attachment-notice {{ background: #fff3cd; padding: 15px; border: 2px dashed #ffc107; 
                                    border-radius: 8px; text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 28px;">🍽️ OMSGr Caterings</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your Ingredients List is Ready!</p>
                </div>
                
                <div class="content">
                    <h2 style="color: #10B981; margin-top: 0;">Dear {customer_name},</h2>
                    <p>Good news! Your ingredients list has been finalized and is ready for review.</p>
                    
                    <div class="attachment-notice">
                        <h3 style="margin: 0 0 10px 0; color: #856404;">📎 PDF Attached</h3>
                        <p style="margin: 0;">Please find your complete ingredients list attached to this email as a PDF document.</p>
                    </div>
                    
                    <div class="details">
                        <h3 style="margin-top: 0; color: #495057;">📋 Event Details</h3>
                        <table>
                            <tr>
                                <td>Booking ID:</td>
                                <td><strong>{booking_id_display}</strong></td>
                            </tr>
                            <tr>
                                <td>Event Date:</td>
                                <td>{booking_details.get('event_date', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Time Slot:</td>
                                <td>{booking_details.get('time_slot', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Number of Guests:</td>
                                <td>{booking_details.get('guests', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td>Event Location:</td>
                                <td>{booking_details.get('event_location', 'N/A')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="highlight">
                        <strong>✅ Important Instructions:</strong>
                        <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                            <li>Please review the attached PDF carefully</li>
                            <li>Ensure all ingredients are fresh and of good quality</li>
                            <li>Keep all items ready at the venue before our team arrives</li>
                            <li>Store perishable items properly until the event</li>
                            <li>Contact us immediately if you have any questions</li>
                        </ul>
                    </div>
                    
                    <p><strong>Need Help?</strong><br>
                    If you have any questions about the ingredients list or need clarification:</p>
                    <ul style="list-style: none; padding: 0;">
                        <li>📞 Phone: +91-XXXXXXXXXX</li>
                        <li>📧 Email: info@omsgrcaterings.com</li>
                    </ul>
                    
                    <p style="margin-top: 30px;">We're looking forward to making your event a success!</p>
                    <p>Best regards,<br><strong>OMSGr Caterings Team</strong></p>
                </div>
                
                <div class="footer">
                    <p style="margin: 0;">This email contains important information about your booking.</p>
                    <p style="margin: 5px 0 0 0;">© 2024 OMSGr Caterings. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Prepare PDF attachment
        pdf_buffer.seek(0)
        pdf_data = pdf_buffer.read()
        
        attachments = [{
            'data': pdf_data,
            'filename': f'Ingredients_List_{booking_id_display}.pdf',
            'type': 'application/pdf'
        }]

        # Send email WITH PDF attachment
        send_email_async(validated_email, subject, html_content, attachments=attachments)

        logger.info(f"Ingredients finalization email with PDF sent to {validated_email} for booking {booking_id_display}")
        return {'success': True, 'message': 'Ingredients finalization email with PDF queued for sending'}

    except Exception as e:
        logger.error(f"Ingredients finalization email failed: {str(e)}")
        return {'success': False, 'error': str(e)}


# =========================
# 3. ADMIN NOTIFICATION EMAIL
# =========================

def send_admin_notification(booking_details):
    """
    Send notification to admin about new booking.
    
    Args:
        booking_details: Dictionary with booking information
    
    Returns:
        dict: {'success': True/False, 'message': string}
    """
    try:
        validated_email = validate_email_address(ADMIN_EMAIL)
        if not validated_email:
            return {'success': False, 'error': 'Invalid admin email address'}

        booking_id = booking_details.get('booking_id', booking_details.get('_id', 'N/A'))
        if isinstance(booking_id, str) and len(booking_id) > 12:
            booking_id_display = booking_id[:12]
        else:
            booking_id_display = str(booking_id)

        subject = f"🔔 New Booking Alert - {booking_id_display}"

        pricing = booking_details.get('pricing', {})
        total_amount = pricing.get('total', 0)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1f2937; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e5e5; }}
                .details {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 15px 0; }}
                table {{ width: 100%; }}
                td {{ padding: 6px; border-bottom: 1px solid #dee2e6; }}
                td:first-child {{ font-weight: bold; width: 35%; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">🔔 New Booking Received</h2>
                </div>
                
                <div class="content">
                    <h3>Customer Details:</h3>
                    <div class="details">
                        <table>
                            <tr><td>Name:</td><td>{booking_details.get('customer_name', 'N/A')}</td></tr>
                            <tr><td>Email:</td><td>{booking_details.get('email', 'N/A')}</td></tr>
                            <tr><td>Mobile:</td><td>{booking_details.get('mobile', 'N/A')}</td></tr>
                        </table>
                    </div>
                    
                    <h3>Booking Details:</h3>
                    <div class="details">
                        <table>
                            <tr><td>Booking ID:</td><td><strong>{booking_id_display}</strong></td></tr>
                            <tr><td>Event Date:</td><td>{booking_details.get('event_date', 'N/A')}</td></tr>
                            <tr><td>Time Slot:</td><td>{booking_details.get('time_slot', 'N/A')}</td></tr>
                            <tr><td>Guests:</td><td>{booking_details.get('guests', 'N/A')}</td></tr>
                            <tr><td>Service Type:</td><td>{booking_details.get('service_type', 'N/A')}</td></tr>
                            <tr><td>Food Preference:</td><td>{booking_details.get('food_preference', 'N/A')}</td></tr>
                            <tr><td>Location:</td><td>{booking_details.get('event_location', 'N/A')}</td></tr>
                            <tr style="background: #fff3cd;"><td><strong>Total Amount:</strong></td><td><strong>₹{total_amount:.2f}</strong></td></tr>
                        </table>
                    </div>
                    
                    <p><strong>Action Required:</strong> Please review and process this booking in the admin dashboard.</p>
                </div>
            </div>
        </body>
        </html>
        """

        send_email_async(validated_email, subject, html_content)

        logger.info(f"Admin notification email sent for booking {booking_id_display}")
        return {'success': True, 'message': 'Admin notification email queued for sending'}

    except Exception as e:
        logger.error(f"Admin notification email failed: {str(e)}")
        return {'success': False, 'error': str(e)}


# =========================
# LEGACY/UTILITY FUNCTIONS (Keep for compatibility)
# =========================

def send_email_with_pdf(recipient_email, pdf_data, subject, body_text=None):
    """
    Generic function to send email with PDF attachment.
    Used for manual PDF sharing from admin panel.
    Falls back to Gmail SMTP if SendGrid is not configured.

    Args:
        recipient_email: Recipient's email address
        pdf_data: PDF file data (bytes)
        subject: Email subject
        body_text: Optional email body text

    Returns:
        dict: {'success': True/False, 'error': error_message}
    """
    try:
        validated_email = validate_email_address(recipient_email)
        if not validated_email:
            return {'success': False, 'error': 'Invalid recipient email address'}

        html_content = body_text or """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #EA580C;">OMSGr Caterings</h2>
            <p>Dear Customer,</p>
            <p>Please find attached your ingredients and grocery list for your upcoming event.</p>
            <p>If you have any questions, please don't hesitate to contact us.</p>
            <p>Best regards,<br><strong>OMSGr Caterings Team</strong></p>
            <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
            <p style="font-size: 12px; color: #666;">This is an automated email. Please do not reply to this address.</p>
        </body>
        </html>
        """

        # Try SendGrid first, fallback to Gmail SMTP
        if SENDGRID_API_KEY:
            # Use SendGrid
            attachments = [{
                'data': pdf_data,
                'filename': 'Ingredients_List.pdf',
                'type': 'application/pdf'
            }]
            send_email_async(validated_email, subject, html_content, attachments=attachments)
        else:
            # Fallback to Gmail SMTP
            send_email_via_gmail_smtp(validated_email, subject, html_content, pdf_data)

        return {'success': True, 'message': 'Email queued for sending'}

    except Exception as e:
        logger.error(f"Email with PDF sending failed: {str(e)}")
        return {'success': False, 'error': str(e)}


def send_email_via_gmail_smtp(to_email, subject, html_content, pdf_data):
    """
    Send email with PDF attachment using Gmail SMTP.
    Used as fallback when SendGrid is not configured.

    Args:
        to_email: Recipient's email address
        subject: Email subject
        html_content: HTML email content
        pdf_data: PDF file data (bytes)
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.getenv("MAIL_USERNAME")
        sender_password = os.getenv("MAIL_PASSWORD")

        if not sender_email or not sender_password:
            raise ValueError("Gmail SMTP credentials not configured in environment variables")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add HTML content
        msg.attach(MIMEText(html_content, 'html'))

        # Add PDF attachment
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="Ingredients_List.pdf"')
        msg.attach(part)

        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()

        logger.info(f"Email sent successfully via Gmail SMTP to {to_email}")

    except Exception as e:
        logger.error(f"Gmail SMTP email sending failed: {str(e)}")
        raise
