from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime

def generate_ingredients_pdf(booking_details, ingredients_list):
    """
    Generate professional PDF with:
    - Business header
    - Order details
    - Customer information
    - All ingredients (categorized)
    - Selected dishes
    - Pricing breakdown
    """
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#EA580C'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # ==========================================
    # 1. BUSINESS HEADER
    # ==========================================
    story.append(Paragraph("🍽️ Chetan Catering Services", title_style))
    story.append(Paragraph("Ingredients List & Order Summary", styles['Heading3']))
    story.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # 2. ORDER INFORMATION
    # ==========================================
    story.append(Paragraph("📋 Order Details", heading_style))
    
    order_data = [
        ['Booking ID:', booking_details.get('_id', 'N/A')[:12]],
        ['Order Date:', datetime.now().strftime('%B %d, %Y')],
        ['Event Date:', booking_details.get('event_date', 'N/A')],
        ['Time Slot:', booking_details.get('time_slot', 'N/A')],
        ['Number of Guests:', str(booking_details.get('guests', 0))],
        ['Service Type:', booking_details.get('service_type', 'N/A')],
        ['Food Preference:', booking_details.get('food_preference', 'N/A')]
    ]
    
    order_table = Table(order_data, colWidths=[2*inch, 4*inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(order_table)
    story.append(Spacer(1, 0.3*inch))
    
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
    
    customer_table = Table(customer_data, colWidths=[2*inch, 4*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(customer_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # 4. SELECTED DISHES
    # ==========================================
    story.append(Paragraph("🍛 Selected Dishes", heading_style))
    
    dishes_data = [['Dish Name', 'Quantity', 'Price/Plate', 'Total']]
    dishes = booking_details.get('dishes', [])
    
    for dish in dishes:
        dishes_data.append([
            dish.get('dish_name', 'N/A'),
            str(dish.get('quantity', 0)),
            f"₹{dish.get('price_per_plate', 0):.2f}",
            f"₹{dish.get('total', 0):.2f}"
        ])
    
    dishes_table = Table(dishes_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
    dishes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EA580C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(dishes_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # 5. INGREDIENTS LIST (CATEGORIZED)
    # ==========================================
    story.append(Paragraph("🥬 Required Ingredients", heading_style))
    
    # Categorize ingredients
    categories = {
        'Vegetables': [],
        'Non-Vegetarian': [],
        'Spices': [],
        'Others': []
    }
    
    for ing in ingredients_list:
        category = ing.get('category', 'Others')
        if category not in categories:
            category = 'Others'
        categories[category].append(ing)
    
    # Render each category
    for category, items in categories.items():
        if not items:
            continue
            
        # Category header
        category_icons = {
            'Vegetables': '🥬',
            'Non-Vegetarian': '🍗',
            'Spices': '🌶️',
            'Others': '🧂'
        }
        icon = category_icons.get(category, '📦')
        
        story.append(Paragraph(f"{icon} {category}", styles['Heading4']))
        
        # Ingredients table
        ing_data = [['Ingredient', 'Quantity', 'Unit', 'Status']]
        
        for ing in items:
            checked = '✅' if ing.get('checked', True) else '⬜'
            ing_data.append([
                ing.get('name', 'N/A'),
                str(ing.get('quantity', 0)),
                ing.get('unit', 'gm'),
                checked
            ])
        
        ing_table = Table(ing_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
        ing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(ing_table)
        story.append(Spacer(1, 0.15*inch))
    
    # ==========================================
    # 6. PRICING BREAKDOWN
    # ==========================================
    story.append(Paragraph("💰 Pricing Summary", heading_style))
    
    pricing = booking_details.get('pricing', {})
    pricing_data = [
        ['Subtotal:', f"₹{pricing.get('subtotal', 0):.2f}"],
        ['Service Charge (10%):', f"₹{pricing.get('service_charge', 0):.2f}"],
        ['GST (5%):', f"₹{pricing.get('gst', 0):.2f}"],
        ['', ''],  # Separator
        ['TOTAL AMOUNT:', f"₹{pricing.get('total', 0):.2f}"]
    ]
    
    pricing_table = Table(pricing_data, colWidths=[4*inch, 2*inch])
    pricing_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 3), 'Helvetica'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 3), 10),
        ('FONTSIZE', (0, 4), (-1, 4), 14),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.HexColor('#EA580C')),
        ('LINEABOVE', (0, 4), (-1, 4), 2, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(pricing_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # 7. FOOTER
    # ==========================================
    footer_text = """
    <para align=center>
    <b>Thank you for choosing Chetan Catering Services!</b><br/>
    For any queries, contact us at: info@chetancatering.com | +91-XXXXXXXXXX<br/>
    <i>Generated on: """ + datetime.now().strftime('%B %d, %Y at %I:%M %p') + """</i>
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer