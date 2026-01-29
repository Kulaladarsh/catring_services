from flask import Blueprint, request, jsonify, send_file, session
from io import BytesIO
from functools import wraps
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

print("=" * 50)
print("EMAIL CONFIGURATION CHECK:")
print(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME')}")
print(f"MAIL_PASSWORD exists: {bool(os.getenv('MAIL_PASSWORD'))}")
print("=" * 50)

pdf_bp = Blueprint("pdf", __name__, url_prefix="/admin/api/pdf")


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
# GENERATE GROCERY LIST PDF
# =========================

def generate_grocery_pdf(booking_details, ingredients_list):
    """
    Generate a professional grocery/ingredients list PDF
    
    Args:
        booking_details: Dictionary with booking information
        ingredients_list: List of ingredients or string
    
    Returns:
        BytesIO object containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    # Title
    elements.append(Paragraph("🥘 GROCERY & INGREDIENTS LIST", title_style))
    elements.append(Paragraph("OMSGr Caterings", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Customer & Event Details Table
    customer_data = [
        ["Customer Name:", booking_details.get('customer_name', 'N/A')],
        ["Phone:", booking_details.get('mobile', 'N/A')],
        ["Email:", booking_details.get('email', 'N/A')],
        ["Event Date:", booking_details.get('event_date', 'N/A')],
        ["Time Slot:", booking_details.get('time_slot', 'N/A')],
        ["Number of Guests:", str(booking_details.get('guests', 'N/A'))],
        ["Location:", booking_details.get('event_location', 'N/A')],
    ]
    
    customer_table = Table(customer_data, colWidths=[2*inch, 4.5*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(customer_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Ingredients Section
    elements.append(Paragraph("📋 INGREDIENTS REQUIRED", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Format ingredients list
    if isinstance(ingredients_list, list):
        ingredients_data = [["Sr. No.", "Item", "Quantity/Details"]]
        for idx, item in enumerate(ingredients_list, 1):
            # Try to split item into name and quantity
            if '-' in item:
                parts = item.split('-', 1)
                ingredients_data.append([str(idx), parts[0].strip(), parts[1].strip()])
            else:
                ingredients_data.append([str(idx), item, "As required"])
    else:
        # If string, split by newlines
        ingredients_data = [["Sr. No.", "Item", "Quantity/Details"]]
        items = ingredients_list.split('\n')
        for idx, item in enumerate(items, 1):
            if item.strip():
                if '-' in item:
                    parts = item.split('-', 1)
                    ingredients_data.append([str(idx), parts[0].strip(), parts[1].strip()])
                else:
                    ingredients_data.append([str(idx), item.strip(), "As required"])
    
    ingredients_table = Table(ingredients_data, colWidths=[0.7*inch, 3*inch, 2.8*inch])
    ingredients_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        
        # Borders and padding
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(ingredients_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Important Notes
    elements.append(Paragraph("⚠️ IMPORTANT NOTES", heading_style))
    notes_text = """
    • Please ensure all ingredients are fresh and of good quality<br/>
    • Keep all items ready at the venue before our team arrives<br/>
    • Store perishable items properly until the event<br/>
    • Contact us immediately if you have any questions or concerns<br/>
    • Our team will handle all the cooking and preparation<br/>
    """
    elements.append(Paragraph(notes_text, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        spaceAfter=5
    )
    
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", footer_style))
    elements.append(Paragraph("<b>OMSGr Caterings</b>", footer_style))
    elements.append(Paragraph("📍 Siddakatte, Karnataka | 📞 +91 98765 43210", footer_style))
    elements.append(Paragraph("📧 chetanpoojary@gmail.com", footer_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


# =========================
# API ENDPOINT: GENERATE PDF
# =========================

@pdf_bp.route("/generate-grocery-list", methods=["POST"])
@admin_required
def generate_grocery_list_pdf():
    """
    Admin API: Generate a grocery list PDF
    """
    try:
        data = request.get_json()

        booking_details = data.get('booking_details', {})
        ingredients = data.get('ingredients', [])

        if not booking_details or not ingredients:
            return jsonify({"error": "booking_details and ingredients are required"}), 400

        # Generate PDF - FIXED: removed booking_id parameter
        pdf_buffer = generate_grocery_pdf(booking_details, ingredients)

        # Generate filename
        customer_name = booking_details.get('customer_name', 'Customer').replace(' ', '_')
        event_date = booking_details.get('event_date', 'date').replace('-', '')
        filename = f"Grocery_List_{customer_name}_{event_date}.pdf"

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500


# =========================
# API ENDPOINT: GENERATE & EMAIL PDF
# =========================

@pdf_bp.route("/generate-and-email", methods=["POST"])
@admin_required
def generate_and_email_pdf():
    """
    Admin API: Generate PDF and send via email
    """
    try:
        data = request.get_json()

        print("📥 Received request data:", data)  # DEBUG

        booking_details = data.get('booking_details', {})
        ingredients = data.get('ingredients', [])
        recipient_email = data.get('recipient_email')

        print(f"📧 Recipient email: {recipient_email}")  # DEBUG
        print(f"📋 Ingredients count: {len(ingredients)}")  # DEBUG

        if not all([booking_details, ingredients, recipient_email]):
            missing = []
            if not booking_details: missing.append('booking_details')
            if not ingredients: missing.append('ingredients')
            if not recipient_email: missing.append('recipient_email')
            error_msg = f"Missing required fields: {', '.join(missing)}"
            print(f"❌ Validation error: {error_msg}")  # DEBUG
            return jsonify({"error": error_msg}), 400

        # Generate PDF
        print("📄 Generating PDF...")  # DEBUG
        pdf_buffer = generate_grocery_pdf(booking_details, ingredients)
        pdf_data = pdf_buffer.getvalue()
        print(f"✅ PDF generated, size: {len(pdf_data)} bytes")  # DEBUG

        # Import email function
        print("📨 Importing email function...")  # DEBUG
        from backend.utils.email import send_email_with_pdf

        # Send email
        print(f"📤 Sending email to {recipient_email}...")  # DEBUG
        result = send_email_with_pdf(
            recipient_email=recipient_email,
            pdf_data=pdf_data,
            subject=f"Grocery List - {booking_details.get('customer_name', 'Customer')}",
            body_text=None
        )

        print(f"📬 Email result: {result}")  # DEBUG

        if result.get('success'):
            return jsonify({
                "success": True,
                "message": f"PDF generated and sent to {recipient_email}"
            })
        else:
            error_message = result.get('error', 'Unknown error occurred')
            print(f"❌ Email failed: {error_message}")  # DEBUG

            # Check for Gmail authentication errors
            if '5.7.8' in error_message or 'Username and Password not accepted' in error_message:
                return jsonify({
                    "success": False,
                    "error": "Gmail authentication failed. Please check your Gmail App Password in .env file."
                }), 401
            else:
                return jsonify({
                    "success": False,
                    "error": error_message
                }), 500

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"💥 Exception occurred:\n{error_trace}")  # DEBUG
        return jsonify({"error": f"Operation failed: {str(e)}"}), 500


# =========================
# API ENDPOINT: PREVIEW PDF DATA
# =========================

@pdf_bp.route("/preview", methods=["POST"])
@admin_required
def preview_pdf():
    """
    Admin API: Preview PDF in browser (returns PDF for inline viewing)
    """
    try:
        data = request.get_json()
        
        booking_details = data.get('booking_details', {})
        ingredients = data.get('ingredients', [])
        
        if not booking_details or not ingredients:
            return jsonify({"error": "booking_details and ingredients are required"}), 400
        
        # Generate PDF
        pdf_buffer = generate_grocery_pdf(booking_details, ingredients)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=False  # Inline viewing
        )
        
    except Exception as e:
        return jsonify({"error": f"PDF preview failed: {str(e)}"}), 500


# =========================
# API ENDPOINT: TEST EMAIL
# =========================

@pdf_bp.route("/test-email", methods=["POST"])
@admin_required
def test_email():
    """
    Test email configuration
    """
    try:
        data = request.get_json()
        test_email = data.get('email', os.getenv('MAIL_USERNAME'))

        import smtplib
        from email.mime.text import MIMEText

        sender_email = os.getenv("MAIL_USERNAME")
        sender_password = os.getenv("MAIL_PASSWORD")

        print(f"Testing email with:")
        print(f"  Sender: {sender_email}")
        print(f"  Password exists: {bool(sender_password)}")
        print(f"  Recipient: {test_email}")

        if not sender_email or not sender_password:
            return jsonify({
                "success": False,
                "error": "Email credentials not configured in .env file"
            }), 500

        msg = MIMEText("This is a test email from Catering Services.")
        msg['Subject'] = 'Test Email'
        msg['From'] = sender_email
        msg['To'] = test_email

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)  # Show SMTP debug info
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        return jsonify({
            "success": True,
            "message": f"Test email sent successfully to {test_email}"
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
