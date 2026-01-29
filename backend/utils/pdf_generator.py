from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime

def generate_ingredients_finalization_pdf(booking_details, ingredients_list):
    """
    Generate professional PDF for finalized ingredients with:
    - Business header with company name "OMSGr Caterings"
    - Order details
    - Customer information
    - Categorized ingredients list
    - Selected dishes
    - Pricing breakdown
    - Production-safe (no truncation, auto page breaks)
    - A4 format
    
    Args:
        booking_details: Dictionary with booking information
        ingredients_list: List of finalized ingredients with category, name, quantity, unit
    
    Returns:
        BytesIO object containing the PDF
    """
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor('#EA580C'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#6B7280'),
        spaceAfter=25,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=15,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )
    
    category_heading_style = ParagraphStyle(
        'CategoryHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#374151'),
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # ==========================================
    # 1. BUSINESS HEADER
    # ==========================================
    story.append(Paragraph("🍽️ OMSGr Caterings", title_style))
    story.append(Paragraph("Finalized Ingredients List & Order Summary", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    # ==========================================
    # 2. ORDER INFORMATION
    # ==========================================
    story.append(Paragraph("📋 Order Details", heading_style))
    
    booking_id = booking_details.get('_id', booking_details.get('booking_id', 'N/A'))
    if isinstance(booking_id, str) and len(booking_id) > 12:
        booking_id_display = booking_id[:12]
    else:
        booking_id_display = str(booking_id)
    
    order_data = [
        ['Booking ID:', booking_id_display],
        ['Order Date:', datetime.now().strftime('%B %d, %Y')],
        ['Event Date:', booking_details.get('event_date', 'N/A')],
        ['Time Slot:', booking_details.get('time_slot', 'N/A')],
        ['Number of Guests:', str(booking_details.get('guests', 0))],
        ['Service Type:', booking_details.get('service_type', 'N/A')],
        ['Food Preference:', booking_details.get('food_preference', 'N/A')]
    ]
    
    order_table = Table(order_data, colWidths=[2.2*inch, 4.3*inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(order_table)
    story.append(Spacer(1, 0.25*inch))
    
    # ==========================================
    # 3. CUSTOMER INFORMATION
    # ==========================================
    story.append(Paragraph("👤 Customer Information", heading_style))
    
    customer_data = [
        ['Name:', booking_details.get('customer_name', 'N/A')],
        ['Mobile:', booking_details.get('mobile', 'N/A')],
        ['Email:', booking_details.get('email', 'N/A')],
        ['Event Location:', booking_details.get('event_location', 'N/A')]
    ]
    
    customer_table = Table(customer_data, colWidths=[2.2*inch, 4.3*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(customer_table)
    story.append(Spacer(1, 0.25*inch))
    
    # ==========================================
    # 4. SELECTED DISHES
    # ==========================================
    story.append(Paragraph("🍛 Selected Dishes", heading_style))
    
    dishes_data = [['Dish Name', 'Quantity', 'Price/Plate', 'Total']]
    dishes = booking_details.get('dishes', [])
    
    if dishes:
        for dish in dishes:
            dishes_data.append([
                Paragraph(dish.get('dish_name', 'N/A'), styles['Normal']),
                str(dish.get('quantity', 0)),
                f"₹{dish.get('price_per_plate', 0):.2f}",
                f"₹{dish.get('total', 0):.2f}"
            ])
    else:
        dishes_data.append(['No dishes selected', '', '', ''])
    
    dishes_table = Table(dishes_data, colWidths=[2.8*inch, 1.2*inch, 1.3*inch, 1.2*inch])
    dishes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EA580C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(dishes_table)
    story.append(Spacer(1, 0.25*inch))
    
    # ==========================================
    # 5. FINALIZED INGREDIENTS LIST (CATEGORIZED)
    # ==========================================
    story.append(Paragraph("🥬 Finalized Ingredients List", heading_style))
    story.append(Paragraph("Please ensure all ingredients are fresh and ready at the venue before our team arrives.", styles['Normal']))
    story.append(Spacer(1, 0.15*inch))
    
    # Categorize ingredients
    categories = {}
    
    for ing in ingredients_list:
        category = ing.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append(ing)
    
    # Define category order for better organization
    category_order = [
        'Vegetables',
        'Non-Vegetarian',
        'Spices / Masala',
        'Dairy',
        'Fruit',
        'Dry Fruits',
        'Grain',
        'Herbs',
        'Beverages',
        'Oil and Fats',
        'Bakery & Sweets',
        'Other'
    ]
    
    # Category icons mapping
    category_icons = {
        'Vegetables': '🥬',
        'Non-Vegetarian': '🍗',
        'Spices / Masala': '🌶️',
        'Dairy': '🥛',
        'Fruit': '🍎',
        'Dry Fruits': '🥜',
        'Grain': '🌾',
        'Herbs': '🌿',
        'Beverages': '🥤',
        'Oil and Fats': '🫒',
        'Bakery & Sweets': '🍰',
        'Other': '📦'
    }
    
    # Render each category
    for category in category_order:
        items = categories.get(category, [])
        if not items:
            continue
        
        # Category header
        icon = category_icons.get(category, '📦')
        story.append(Paragraph(f"{icon} {category}", category_heading_style))
        
        # Ingredients table for this category
        ing_data = [['Ingredient', 'Quantity', 'Unit', 'Status']]
        
        for ing in items:
            checked = '✅' if ing.get('checked', True) else '⬜'
            quantity = ing.get('quantity', 0)
            
            # Format quantity properly
            if isinstance(quantity, float):
                if quantity == int(quantity):
                    quantity_str = str(int(quantity))
                else:
                    quantity_str = f"{quantity:.2f}"
            else:
                quantity_str = str(quantity)
            
            ing_data.append([
                Paragraph(ing.get('name', 'N/A'), styles['Normal']),
                quantity_str,
                ing.get('unit', 'gm'),
                checked
            ])
        
        ing_table = Table(ing_data, colWidths=[2.8*inch, 1.3*inch, 1.2*inch, 1.2*inch])
        ing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        
        # Use KeepTogether to prevent category from splitting across pages
        story.append(KeepTogether([ing_table, Spacer(1, 0.12*inch)]))
    
    # ==========================================
    # 6. PRICING BREAKDOWN
    # ==========================================
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("💰 Pricing Summary", heading_style))
    
    pricing = booking_details.get('pricing', {})
    subtotal = pricing.get('subtotal', 0)
    service_charge = pricing.get('service_charge', 0)
    gst = pricing.get('gst', 0)
    total = pricing.get('total', 0)
    
    pricing_data = [
        ['Subtotal:', f"₹{subtotal:.2f}"],
        ['Service Charge (10%):', f"₹{service_charge:.2f}"],
        ['GST (5%):', f"₹{gst:.2f}"],
        ['', ''],  # Separator
        ['TOTAL AMOUNT:', f"₹{total:.2f}"]
    ]
    
    pricing_table = Table(pricing_data, colWidths=[4.5*inch, 2*inch])
    pricing_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 3), 'Helvetica'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 3), 11),
        ('FONTSIZE', (0, 4), (-1, 4), 15),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.HexColor('#EA580C')),
        ('LINEABOVE', (0, 4), (-1, 4), 2, colors.HexColor('#1F2937')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(pricing_table)
    story.append(Spacer(1, 0.25*inch))
    
    # ==========================================
    # 7. IMPORTANT NOTES
    # ==========================================
    story.append(Paragraph("⚠️ Important Notes", heading_style))
    
    notes_style = ParagraphStyle(
        'Notes',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        leftIndent=15
    )
    
    notes = [
        "• Please ensure all ingredients are fresh and of good quality",
        "• Keep all items ready at the venue before our team arrives",
        "• Store perishable items properly until the event",
        "• Contact us immediately if you have any questions or concerns",
        "• Our team will handle all the cooking and preparation"
    ]
    
    for note in notes:
        story.append(Paragraph(note, notes_style))
    
    story.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # 8. FOOTER
    # ==========================================
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER,
        spaceAfter=4
    )
    
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("─" * 80, footer_style))
    story.append(Paragraph("<b>OMSGr Caterings</b>", footer_style))
    story.append(Paragraph("📍 Siddakatte, Karnataka | 📞 +91-XXXXXXXXXX", footer_style))
    story.append(Paragraph("📧 info@omsgrcaterings.com", footer_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    
    # Build PDF with error handling
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error building PDF: {e}")
        raise