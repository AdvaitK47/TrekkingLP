"""
Script to generate a publication-quality Entity-Relationship (ER) Model PDF
for the MOUNTAINS Trekking & Expedition Management System (PostgreSQL DBMS).
Uses Pillow for diagram rendering and ReportLab for multi-page PDF generation.
"""

import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, NextPageTemplate, HRFlowable
)
from reportlab.pdfgen import canvas


# -------------------------------------------------------------
# STEP 1: RENDER ULTRA HIGH-RESOLUTION ER DIAGRAM IMAGE (PNG)
# -------------------------------------------------------------
def generate_er_diagram_image(output_path="er_diagram.png"):
    W, H = 3600, 2300
    img = Image.new("RGBA", (W, H), (10, 15, 23, 255))
    draw = ImageDraw.Draw(img)

    def get_font(size, bold=False):
        font_names = [
            "segoeuib.ttf" if bold else "segoeui.ttf",
            "arialbd.ttf" if bold else "arial.ttf",
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        ]
        for name in font_names:
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return ImageFont.load_default()

    font_title = get_font(46, bold=True)
    font_sub = get_font(23, bold=False)
    font_entity_header = get_font(28, bold=True)
    font_attr_name = get_font(20, bold=False)
    font_attr_bold = get_font(20, bold=True)
    font_attr_type = get_font(18, bold=False)
    font_badge = get_font(15, bold=True)
    font_rel = get_font(17, bold=True)
    font_card = get_font(22, bold=True)

    # Subtle Background Blueprint Grid
    grid_color = (255, 255, 255, 10)
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # Header Box
    draw.rounded_rectangle([60, 40, W - 60, 150], radius=16, fill=(18, 26, 40, 255), outline=(51, 65, 85, 255), width=2)
    draw.text((90, 56), "MOUNTAINS - TREKKING MANAGEMENT SYSTEM", font=font_title, fill=(245, 158, 11, 255))
    draw.text((90, 110), "Relational Entity-Relationship (ER) Logical Schema • PostgreSQL Relational Database Engine • 7 Normalized Core Entities", font=font_sub, fill=(148, 163, 184, 255))

    # Entities Definition
    entities = {
        "users": {
            "x": 100, "y": 210, "w": 460, "h": 540,
            "title": "USERS",
            "color": (30, 58, 138),  # Deep Blue
            "attrs": [
                (True, False, "id", "SERIAL [PK]"),
                (False, False, "name", "VARCHAR(120)"),
                (False, False, "username", "VARCHAR(80) UNIQUE"),
                (False, False, "email", "VARCHAR(120) UNIQUE"),
                (False, False, "contact", "VARCHAR(20)"),
                (False, False, "emergency_name", "VARCHAR(120)"),
                (False, False, "emergency_phone", "VARCHAR(20)"),
                (False, False, "password_hash", "VARCHAR(255)"),
                (False, False, "role", "VARCHAR(10) CHECK"),
                (False, False, "status", "VARCHAR(12) CHECK"),
                (False, False, "created_at", "TIMESTAMP")
            ]
        },
        "treks": {
            "x": 1400, "y": 210, "w": 520, "h": 720,
            "title": "TREKS",
            "color": (217, 119, 6),  # Amber Mountain
            "attrs": [
                (True, False, "id", "SERIAL [PK]"),
                (False, False, "name", "VARCHAR(150)"),
                (False, False, "destination", "VARCHAR(150)"),
                (False, False, "location", "VARCHAR(150)"),
                (False, False, "difficulty", "VARCHAR(10) CHECK"),
                (False, False, "duration", "INTEGER (Days)"),
                (False, False, "base_cost", "NUMERIC(10,2)"),
                (False, False, "price", "NUMERIC(10,2)"),
                (False, False, "max_capacity", "INTEGER"),
                (False, False, "total_slots", "INTEGER"),
                (False, True,  "assigned_staff_id", "INT -> users.id [FK]"),
                (False, False, "status", "VARCHAR(10) CHECK"),
                (False, False, "start_date", "DATE"),
                (False, False, "end_date", "DATE"),
                (False, False, "is_trending", "BOOLEAN"),
                (False, False, "category", "VARCHAR(50) CHECK")
            ]
        },
        "bookings": {
            "x": 750, "y": 570, "w": 480, "h": 490,
            "title": "BOOKINGS",
            "color": (5, 150, 105),  # Emerald Green
            "attrs": [
                (True, False, "id", "SERIAL [PK]"),
                (False, True,  "user_id", "INT -> users.id [FK]"),
                (False, True,  "trek_id", "INT -> treks.id [FK]"),
                (False, False, "travel_date", "DATE"),
                (False, False, "num_participants", "INTEGER >= 1"),
                (False, False, "total_price", "NUMERIC(10,2)"),
                (False, False, "status", "VARCHAR(15) CHECK"),
                (False, False, "special_requests", "TEXT"),
                (False, False, "booking_date", "TIMESTAMP")
            ]
        },
        "transactions": {
            "x": 750, "y": 1300, "w": 480, "h": 410,
            "title": "TRANSACTIONS",
            "color": (124, 58, 237),  # Purple Violet
            "attrs": [
                (True, False, "id", "SERIAL [PK]"),
                (False, True,  "booking_id", "INT -> bookings.id [FK]"),
                (False, False, "transaction_id", "VARCHAR(100) UNIQUE"),
                (False, False, "amount", "NUMERIC(10,2)"),
                (False, False, "payment_method", "VARCHAR(50)"),
                (False, False, "status", "VARCHAR(20) CHECK"),
                (False, False, "created_at", "TIMESTAMP")
            ]
        },
        "shops": {
            "x": 2850, "y": 320, "w": 500, "h": 470,
            "title": "SHOPS",
            "color": (2, 132, 199),  # Sky Blue
            "attrs": [
                (True, False, "id", "SERIAL [PK]"),
                (False, False, "name", "VARCHAR(150)"),
                (False, False, "category", "VARCHAR(50) CHECK"),
                (False, False, "coordinates", "VARCHAR(100)"),
                (False, False, "contact_number", "VARCHAR(30)"),
                (False, False, "rating", "NUMERIC(2,1)"),
                (False, True,  "trek_id", "INT -> treks.id [FK]"),
                (False, False, "created_at", "TIMESTAMP")
            ]
        },
        "rescue_operations": {
            "x": 1400, "y": 1280, "w": 550, "h": 530,
            "title": "RESCUE_OPERATIONS",
            "color": (220, 38, 38),  # Crimson Red
            "attrs": [
                (True, False, "id", "SERIAL [PK]"),
                (False, True,  "trekker_id", "INT -> users.id [FK]"),
                (False, True,  "staff_id", "INT -> users.id [FK]"),
                (False, True,  "trek_id", "INT -> treks.id [FK]"),
                (False, False, "emergency_type", "VARCHAR(100)"),
                (False, False, "last_coordinates", "VARCHAR(100)"),
                (False, False, "alert_time", "TIMESTAMP"),
                (False, False, "status", "VARCHAR(30) CHECK"),
                (False, False, "notes", "TEXT"),
                (False, False, "updated_at", "TIMESTAMP")
            ]
        },
        "reviews": {
            "x": 2220, "y": 960, "w": 480, "h": 430,
            "title": "REVIEWS",
            "color": (234, 88, 12),  # Sunset Orange
            "attrs": [
                (True, False, "id", "SERIAL [PK]"),
                (False, True,  "user_id", "INT -> users.id [FK]"),
                (False, True,  "trek_id", "INT -> treks.id [FK]"),
                (False, False, "rating", "INTEGER (1..5)"),
                (False, False, "comment", "TEXT"),
                (False, False, "is_featured", "BOOLEAN"),
                (False, False, "created_at", "TIMESTAMP")
            ]
        }
    }

    # Draw Each Entity Card
    for key, ent in entities.items():
        x, y, w, h = ent["x"], ent["y"], ent["w"], ent["h"]
        draw.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=(17, 24, 39, 255), outline=(51, 65, 85, 255), width=2)
        header_h = 60
        draw.rounded_rectangle([x, y, x + w, y + header_h], radius=16, fill=ent["color"] + (255,))
        draw.rectangle([x, y + header_h - 16, x + w, y + header_h], fill=ent["color"] + (255,))
        draw.text((x + 22, y + 14), ent["title"], font=font_entity_header, fill=(255, 255, 255, 255))
        draw.rounded_rectangle([x + w - 95, y + 16, x + w - 20, y + 44], radius=8, fill=(0, 0, 0, 100))
        draw.text((x + w - 85, y + 20), "TABLE", font=font_badge, fill=(241, 245, 249, 255))

        curr_y = y + header_h + 16
        for is_pk, is_fk, name, atype in ent["attrs"]:
            draw.line([(x + 14, curr_y + 28), (x + w - 14, curr_y + 28)], fill=(255, 255, 255, 12), width=1)
            if is_pk:
                draw.rounded_rectangle([x + 16, curr_y - 2, x + 54, curr_y + 22], radius=4, fill=(217, 119, 6, 220))
                draw.text((x + 22, curr_y + 2), "PK", font=font_badge, fill=(255, 255, 255, 255))
                draw.text((x + 64, curr_y), name, font=font_attr_bold, fill=(251, 191, 36, 255))
            elif is_fk:
                draw.rounded_rectangle([x + 16, curr_y - 2, x + 54, curr_y + 22], radius=4, fill=(14, 165, 233, 220))
                draw.text((x + 22, curr_y + 2), "FK", font=font_badge, fill=(255, 255, 255, 255))
                draw.text((x + 64, curr_y), name, font=font_attr_bold, fill=(56, 189, 248, 255))
            else:
                draw.ellipse([x + 28, curr_y + 6, x + 38, curr_y + 16], fill=(148, 163, 184, 190))
                draw.text((x + 64, curr_y), name, font=font_attr_name, fill=(226, 232, 240, 255))

            draw.text((x + w - 200, curr_y + 2), atype[:20], font=font_attr_type, fill=(148, 163, 184, 255))
            curr_y += 38

    # -------------------------------------------------------------
    # RELATIONSHIP CONNECTORS & CARDINALITIES
    # -------------------------------------------------------------
    def draw_rel_line(points, label, c1, c2, color=(148, 163, 184, 255), label_pos=None):
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color, width=4)
        draw.text(points[0], c1, font=font_card, fill=(251, 191, 36, 255))
        draw.text(points[-1], c2, font=font_card, fill=(56, 189, 248, 255))
        if label_pos:
            lx, ly = label_pos
            lw, lh = len(label) * 12 + 28, 34
            draw.rounded_rectangle([lx - lw//2, ly - lh//2, lx + lw//2, ly + lh//2], radius=12, fill=(30, 41, 59, 255), outline=color, width=2)
            draw.text((lx - lw//2 + 14, ly - 9), label, font=font_rel, fill=(248, 250, 252, 255))

    # 1. USERS (1) -> (N) BOOKINGS
    draw_rel_line(
        [(560, 480), (655, 480), (655, 720), (750, 720)],
        "places (1:N)", "1", "N",
        color=(5, 150, 105, 240), label_pos=(655, 600)
    )

    # 2. TREKS (1) -> (N) BOOKINGS
    draw_rel_line(
        [(1400, 620), (1315, 620), (1315, 760), (1230, 760)],
        "reserves (1:N)", "1", "N",
        color=(217, 119, 6, 240), label_pos=(1315, 690)
    )

    # 3. BOOKINGS (1) -> (1) TRANSACTIONS
    draw_rel_line(
        [(990, 1060), (990, 1300)],
        "generates (1:1)", "1", "1",
        color=(124, 58, 237, 240), label_pos=(990, 1180)
    )

    # 4. USERS (1: Staff) -> (N) TREKS
    draw_rel_line(
        [(560, 320), (980, 320), (980, 250), (1400, 250)],
        "guides / leads (1:N)", "1", "N",
        color=(56, 189, 248, 240), label_pos=(980, 285)
    )

    # 5. TREKS (1) -> (N) SHOPS
    draw_rel_line(
        [(1920, 440), (2850, 440)],
        "partners / hosts (1:N)", "1", "N",
        color=(2, 132, 199, 240), label_pos=(2385, 440)
    )

    # 6. USERS (1) -> (N) REVIEWS
    draw_rel_line(
        [(330, 750), (330, 1140), (2220, 1140)],
        "writes review (1:N)", "1", "N",
        color=(234, 88, 12, 240), label_pos=(540, 1140)
    )

    # 7. TREKS (1) -> (N) REVIEWS
    draw_rel_line(
        [(1920, 720), (2070, 720), (2070, 1020), (2220, 1020)],
        "evaluated_for (1:N)", "1", "N",
        color=(234, 88, 12, 240), label_pos=(2070, 870)
    )

    # 8. USERS (1) -> (N) RESCUE_OPERATIONS
    draw_rel_line(
        [(220, 750), (220, 1540), (1400, 1540)],
        "requests SOS (1:N)", "1", "N",
        color=(220, 38, 38, 240), label_pos=(480, 1540)
    )

    # 9. TREKS (1) -> (N) RESCUE_OPERATIONS
    draw_rel_line(
        [(1660, 930), (1660, 1280)],
        "occurs on route (1:N)", "1", "N",
        color=(220, 38, 38, 240), label_pos=(1660, 1105)
    )

    # -------------------------------------------------------------
    # LEGEND BOX
    # -------------------------------------------------------------
    lx, ly, lw, lh = 2450, 1680, 850, 480
    draw.rounded_rectangle([lx, ly, lx + lw, ly + lh], radius=16, fill=(18, 26, 40, 255), outline=(51, 65, 85, 255), width=2)
    draw.text((lx + 32, ly + 25), "RELATIONAL NOTATION & CONSTRAINTS", font=font_entity_header, fill=(245, 158, 11, 255))
    
    legend_items = [
        ("PK", (217, 119, 6), "Primary Key (Unique, Not-Null Identity Column)"),
        ("FK", (14, 165, 233), "Foreign Key (Referential Integrity Constraint)"),
        ("1:N", (5, 150, 105), "One-to-Many Cardinality (Parent to Child Table)"),
        ("1:1", (124, 58, 237), "One-to-One Strict Relation (Booking to Transaction)"),
        ("CHECK", (220, 38, 38), "Domain Integrity Constraint (Role, Status, Rating)"),
        ("CASCADE", (148, 163, 184), "ON DELETE CASCADE / SET NULL Protection")
    ]
    curr_ly = ly + 80
    for tag, col, desc in legend_items:
        draw.rounded_rectangle([lx + 30, curr_ly - 2, lx + 125, curr_ly + 30], radius=6, fill=col + (220,))
        draw.text((lx + 42, curr_ly + 3), tag, font=font_badge, fill=(255, 255, 255, 255))
        draw.text((lx + 145, curr_ly + 5), desc, font=font_attr_name, fill=(226, 232, 240, 255))
        curr_ly += 48

    # Footer
    draw.text((60, H - 60), "PostgreSQL 16 Relational Engine • Third Normal Form (3NF) • Acid Compliant • MOUNTAINS Expedition Management System", font=font_sub, fill=(100, 116, 139, 255))

    img.save(output_path, "PNG", dpi=(300, 300))
    print(f"[OK] High-Res diagram saved to {output_path}")
    return output_path


# -------------------------------------------------------------
# STEP 2: BUILD COMPREHENSIVE MULTI-PAGE REPORTLAB PDF
# -------------------------------------------------------------
class PageDecoratedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(PageDecoratedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super(PageDecoratedCanvas, self).showPage()
        super(PageDecoratedCanvas, self).save()

    def draw_decorations(self, total_pages):
        self.saveState()
        w, h = self._pagesize
        is_landscape = w > h

        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (Only on portrait pages 3+)
        if not is_landscape and self._pageNumber > 2:
            self.drawString(40, h - 30, "MOUNTAINS Expedition Management System — Relational ER Model Specification")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(40, h - 34, w - 40, h - 34)

        # Footer
        footer_text = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(w - 40, 24, footer_text)
        self.drawString(40, 24, "Confidential — Database Management System (DBMS) Relational Documentation")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 34, w - 40, 34)

        self.restoreState()


def build_er_model_pdf(diagram_image_path, pdf_output_path="Trekking_Management_System_ER_Model.pdf"):
    pw_port, ph_port = letter
    pw_land, ph_land = landscape(letter)

    doc = BaseDocTemplate(
        pdf_output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=44
    )

    frame_port = Frame(36, 44, pw_port - 72, ph_port - 88, id='frame_portrait', topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    frame_land = Frame(30, 36, pw_land - 60, ph_land - 72, id='frame_landscape', topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)

    template_port = PageTemplate(id='Portrait', frames=frame_port, pagesize=letter)
    template_land = PageTemplate(id='Landscape', frames=frame_land, pagesize=landscape(letter))
    doc.addPageTemplates([template_port, template_land])

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#D97706"),
        spaceAfter=12
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=8,
        spaceAfter=5,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#1E293B")
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#0F172A")
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=9.8,
        textColor=colors.white
    )

    story = []

    # =========================================================
    # PAGE 1: COVER & ARCHITECTURE OVERVIEW (PORTRAIT)
    # =========================================================
    story.append(Paragraph("MOUNTAINS EXPEDITION MANAGEMENT SYSTEM", title_style))
    story.append(Paragraph("Relational Database Design Specification & Entity-Relationship (ER) Model", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#D97706"), spaceBefore=0, spaceAfter=8))

    meta_data = [
        [Paragraph("<b>Target DBMS:</b> PostgreSQL 16+ Relational Engine", table_cell), Paragraph("<b>Core Entities:</b> 7 Normalized Relational Tables", table_cell)],
        [Paragraph("<b>Normalization Level:</b> Third Normal Form (3NF)", table_cell), Paragraph("<b>Analytical SQL Views:</b> 4 Live Aggregated Views", table_cell)],
        [Paragraph("<b>Integrity Constraints:</b> 8 Foreign Keys with Cascade/Set Null", table_cell), Paragraph("<b>Security:</b> PBKDF2 Password Hashing & Role RBAC", table_cell)],
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Executive DBMS Architecture Summary", section_heading))
    story.append(Paragraph(
        "The <b>MOUNTAINS</b> database architecture is engineered to provide high-concurrency expedition booking, "
        "comprehensive trekker safety tracking, partner gear hub integration, and 24/7 high-altitude rescue dispatch logistics. "
        "The relational schema is strictly normalized into <b>Third Normal Form (3NF)</b>, eliminating update, insertion, and deletion "
        "anomalies while enforcing ACID compliance for all financial and booking operations.",
        body_style
    ))

    story.append(Paragraph("2. Conceptual Entities & Core System Relationships", section_heading))
    story.append(Paragraph(
        "The system centers around two primary entities: <b>USERS</b> (Trekkers, Certified Mountain Guides, and System Commanders) "
        "and <b>TREKS</b> (Expedition routes, difficulty ratings, capacity quotas, and base pricing). "
        "Transactional operations flow seamlessly through <b>BOOKINGS</b> (reservation agreements) and <b>TRANSACTIONS</b> (audit ledgers). "
        "Supporting operational workflows include <b>SHOPS</b> (partner rental vendors along trails), "
        "<b>RESCUE_OPERATIONS</b> (live GPS distress dispatches), and <b>REVIEWS</b> (verified trekker feedback).",
        body_style
    ))

    story.append(Paragraph("3. Relational Structural Highlights", section_heading))
    story.append(Paragraph(
        "• <b>Primary Keys:</b> Every table utilizes a synthetic integer primary key (<code>SERIAL</code>) for performant join indexes.<br/>"
        "• <b>Referential Integrity:</b> Foreign keys enforce operational reality—e.g. deleting a user is restricted if active bookings exist (<code>ON DELETE RESTRICT</code>), "
        "while deleting a trek cleans up associated itinerary bookings and vendor records (<code>ON DELETE CASCADE</code>).<br/>"
        "• <b>Domain Constraints:</b> Enforced via PostgreSQL <code>CHECK</code> clauses ensuring valid difficulty tiers ('Easy', 'Moderate', 'Hard'), "
        "user roles ('admin', 'staff', 'user'), review star scores (1 to 5), and positive financial amounts.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4. Preview of Logical ER Diagram", section_heading))
    story.append(Paragraph(
        "<i>Please turn to Page 2 for the full-spread, high-resolution landscape diagram with all attribute lists, key badges, and connector routes.</i>",
        body_style
    ))
    diag_preview = RLImage(diagram_image_path, width=540, height=270)
    story.append(diag_preview)

    # =========================================================
    # PAGE 2: FULL SPREAD LANDSCAPE ER DIAGRAM
    # =========================================================
    story.append(NextPageTemplate('Landscape'))
    story.append(PageBreak())

    story.append(Paragraph("<b>Figure 1: Full-Spread Relational Entity-Relationship (ER) Logical Schema</b>", ParagraphStyle('LandTitle', parent=section_heading, fontSize=11, spaceBefore=0, spaceAfter=2)))
    story.append(Paragraph("<font color='#64748B'>PostgreSQL Relational Engine • 7 Normalized Tables • Primary & Foreign Key Connectors • Cardinalities (1:N, 1:1)</font>", ParagraphStyle('LandSub', parent=body_style, fontSize=8, spaceAfter=4)))
    
    diag_full = RLImage(diagram_image_path, width=732, height=450)
    story.append(diag_full)

    # =========================================================
    # PAGE 3: DATA DICTIONARY (ENTITIES 1, 2, 3)
    # =========================================================
    story.append(NextPageTemplate('Portrait'))
    story.append(PageBreak())

    story.append(Paragraph("5. Relational Data Dictionary & Attribute Specifications", section_heading))
    story.append(Paragraph("Comprehensive catalog of tables, column data types, constraints, and operational business rules.", body_style))
    story.append(Spacer(1, 2))

    def render_entity_table(title, subtitle, header_color, rows):
        elements = []
        elements.append(Paragraph(f"<b>{title}</b> — <font color='#64748B'>{subtitle}</font>", ParagraphStyle('ETitle', parent=section_heading, fontSize=9, spaceBefore=3, spaceAfter=2)))
        
        table_rows = [[
            Paragraph("Column", table_header),
            Paragraph("Type", table_header),
            Paragraph("Constraints & Keys", table_header),
            Paragraph("Description & Business Rules", table_header)
        ]]
        for col, dtype, constr, desc in rows:
            is_pk = "PK" in constr
            is_fk = "FK" in constr
            constr_color = "#D97706" if is_pk else ("#0284C7" if is_fk else "#475569")
            table_rows.append([
                Paragraph(f"<b>{col}</b>", table_cell_bold if (is_pk or is_fk) else table_cell),
                Paragraph(dtype, table_cell),
                Paragraph(f"<font color='{constr_color}'><b>{constr}</b></font>", table_cell),
                Paragraph(desc, table_cell)
            ])
            
        t = Table(table_rows, colWidths=[90, 85, 115, 250])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), header_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")])
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4))
        return elements

    # USERS
    users_rows = [
        ("id", "SERIAL", "PRIMARY KEY", "Surrogate unique identity key for each user account."),
        ("name", "VARCHAR(120)", "NOT NULL", "Full legal name of the user / staff guide / administrator."),
        ("username", "VARCHAR(80)", "UNIQUE, NOT NULL", "Unique handle for system authentication and portal login."),
        ("email", "VARCHAR(120)", "UNIQUE, NOT NULL", "User email address for booking invoices and SOS communications."),
        ("contact", "VARCHAR(20)", "NULLABLE", "Direct mobile phone number with international country dialing code."),
        ("emergency_name", "VARCHAR(120)", "NULLABLE", "Next of kin / emergency contact individual name."),
        ("emergency_phone", "VARCHAR(20)", "NULLABLE", "High-priority phone number contacted during emergency rescues."),
        ("password_hash", "VARCHAR(255)", "NOT NULL", "Secure PBKDF2 salted cryptographic password hash."),
        ("role", "VARCHAR(10)", "CHECK (admin, staff, user)", "Role-Based Access Control: 'admin', 'staff', 'user'."),
        ("status", "VARCHAR(12)", "CHECK (approved, pending, ...)", "Account lifecycle: staff requires admin approval before guiding."),
        ("created_at", "TIMESTAMP", "NOT NULL, DEFAULT NOW()", "System audit timestamp indicating when account was registered.")
    ]
    for el in render_entity_table("ENTITY 1: USERS", "Trekkers, Mountain Guides & System Admins", colors.HexColor("#1E3A8A"), users_rows):
        story.append(el)

    # TREKS
    treks_rows = [
        ("id", "SERIAL", "PRIMARY KEY", "Unique expedition identifier."),
        ("name", "VARCHAR(150)", "NOT NULL", "Marketing and official expedition name (e.g. Everest Base Camp)."),
        ("destination", "VARCHAR(150)", "NOT NULL", "Target mountain peak, valley, or country (e.g. Khumbu, Nepal)."),
        ("location", "VARCHAR(150)", "NOT NULL", "Geographical mountain region, state, or starting trailhead."),
        ("difficulty", "VARCHAR(10)", "CHECK (Easy, Moderate, Hard)", "Physical difficulty tier based on altitude, incline, and terrain."),
        ("duration", "INTEGER", "NOT NULL, CHECK (> 0)", "Expedition span in total calendar days."),
        ("base_cost", "NUMERIC(10,2)", "NOT NULL, CHECK (>= 0)", "Base price per trekker for expedition permit and logistics."),
        ("max_capacity", "INTEGER", "NOT NULL, CHECK (> 0)", "Maximum allowable group size for ecological preservation."),
        ("total_slots", "INTEGER", "NOT NULL, CHECK (> 0)", "Configured capacity slots for the upcoming departure date."),
        ("assigned_staff_id", "INTEGER", "FOREIGN KEY -> users.id", "Assigned Lead Alpine Guide (ON DELETE SET NULL)."),
        ("status", "VARCHAR(10)", "CHECK (Open, Closed, Completed)", "Expedition booking status."),
        ("start_date / end_date", "DATE", "CHECK (end >= start)", "Expedition departure and conclusion dates."),
        ("is_trending", "BOOLEAN", "DEFAULT FALSE", "Flag highlighting featured treks on landing page card grid."),
        ("category", "VARCHAR(50)", "CHECK (Adventure, Trekking, ...)", "Trek classification for filtering in Search Tours.")
    ]
    for el in render_entity_table("ENTITY 2: TREKS", "Alpine expeditions catalog with itineraries & guides", colors.HexColor("#D97706"), treks_rows):
        story.append(el)

    # BOOKINGS
    bookings_rows = [
        ("id", "SERIAL", "PRIMARY KEY", "Unique reservation booking number."),
        ("user_id", "INTEGER", "FOREIGN KEY -> users.id", "Trekker placing the reservation (ON DELETE RESTRICT)."),
        ("trek_id", "INTEGER", "FOREIGN KEY -> treks.id", "Reserved expedition route (ON DELETE CASCADE)."),
        ("travel_date", "DATE", "NOT NULL, DEFAULT CURRENT_DATE", "Scheduled departure date for party arrival at basecamp."),
        ("num_participants", "INTEGER", "NOT NULL, CHECK (> 0)", "Number of expedition slots reserved in party."),
        ("total_price", "NUMERIC(10,2)", "NOT NULL, CHECK (>= 0)", "Computed price: num_participants multiplied by trek base_cost."),
        ("status", "VARCHAR(15)", "CHECK (Confirmed, Booked, ...)", "Reservation status: 'Confirmed', 'Booked', 'Cancelled', 'Completed'."),
        ("special_requests", "TEXT", "NULLABLE", "Special trekker dietary, high-altitude gear, or medical requests.")
    ]
    for el in render_entity_table("ENTITY 3: BOOKINGS", "Expedition reservation contracts linking Trekkers to Treks", colors.HexColor("#059669"), bookings_rows):
        story.append(el)

    # =========================================================
    # PAGE 4: DATA DICTIONARY (ENTITIES 4, 5, 6, 7)
    # =========================================================
    story.append(PageBreak())
    story.append(Paragraph("5. Relational Data Dictionary & Attribute Specifications (Continued)", section_heading))
    story.append(Paragraph("Transactional and operational entities supporting financial ledgers, vendor hubs, emergency dispatches, and reviews.", body_style))
    story.append(Spacer(1, 2))

    # TRANSACTIONS
    tx_rows = [
        ("id", "SERIAL", "PRIMARY KEY", "Unique transaction record identifier."),
        ("booking_id", "INTEGER", "FOREIGN KEY -> bookings.id", "Associated booking reservation (ON DELETE CASCADE)."),
        ("transaction_id", "VARCHAR(100)", "UNIQUE, NOT NULL", "External bank reference code or gateway merchant tracking token."),
        ("amount", "NUMERIC(10,2)", "NOT NULL, CHECK (>= 0)", "Processed currency amount."),
        ("payment_method", "VARCHAR(50)", "NOT NULL", "Method: 'Credit Card', 'UPI/NetBanking', 'Apple Pay', 'PayPal'."),
        ("status", "VARCHAR(20)", "CHECK (Success, Pending, ...)", "Financial status: 'Success', 'Pending', 'Refunded', 'Failed'.")
    ]
    for el in render_entity_table("ENTITY 4: TRANSACTIONS", "Financial audit ledger and payment records", colors.HexColor("#7C3AED"), tx_rows):
        story.append(el)

    # SHOPS
    shops_rows = [
        ("id", "SERIAL", "PRIMARY KEY", "Unique vendor shop identifier."),
        ("name", "VARCHAR(150)", "NOT NULL", "Business name of partner shop / rental agency."),
        ("category", "VARCHAR(50)", "CHECK (Gear Rental, Cafe, ...)", "Vendor service category (Gear Rental, Photography, Food, Medical)."),
        ("coordinates", "VARCHAR(100)", "NOT NULL", "GPS coordinates / basecamp trail marker for physically locating shop."),
        ("rating", "NUMERIC(2,1)", "DEFAULT 4.8", "Aggregated customer feedback rating (scale 1.0 to 5.0)."),
        ("trek_id", "INTEGER", "FOREIGN KEY -> treks.id", "Expedition route near which shop operates (ON DELETE CASCADE).")
    ]
    for el in render_entity_table("ENTITY 5: SHOPS", "Vetted gear rental, nutrition and photography basecamp hubs", colors.HexColor("#0284C7"), shops_rows):
        story.append(el)

    # RESCUE OPERATIONS
    rescue_rows = [
        ("id", "SERIAL", "PRIMARY KEY", "Unique emergency dispatch incident identifier."),
        ("trekker_id", "INTEGER", "FOREIGN KEY -> users.id", "Distressed trekker needing emergency evacuation (ON DELETE CASCADE)."),
        ("staff_id", "INTEGER", "FOREIGN KEY -> users.id", "Assigned certified alpine guide/commander (ON DELETE SET NULL)."),
        ("trek_id", "INTEGER", "FOREIGN KEY -> treks.id", "Expedition route where distress occurred (ON DELETE SET NULL)."),
        ("emergency_type", "VARCHAR(100)", "NOT NULL", "Category: AMS Medical, Blizzard Stranded, Injury/Fall, Equipment."),
        ("last_coordinates", "VARCHAR(100)", "NOT NULL", "Live GPS coordinates broadcast via Auto-GPS or landmark description."),
        ("status", "VARCHAR(30)", "CHECK (Active, Dispatched, ...)", "Operation lifecycle: 'Active', 'Dispatched', 'Evacuated', 'Resolved'.")
    ]
    for el in render_entity_table("ENTITY 6: RESCUE_OPERATIONS", "24/7 High-Altitude Emergency Logistics & SOS Dispatch", colors.HexColor("#DC2626"), rescue_rows):
        story.append(el)

    # REVIEWS
    reviews_rows = [
        ("id", "SERIAL", "PRIMARY KEY", "Unique review identifier."),
        ("user_id", "INTEGER", "FOREIGN KEY -> users.id", "Verified trekker authoring the review (ON DELETE CASCADE)."),
        ("trek_id", "INTEGER", "FOREIGN KEY -> treks.id", "Expedition route evaluated (ON DELETE CASCADE)."),
        ("rating", "INTEGER", "CHECK (>= 1 AND <= 5)", "Numerical star rating from 1 (Poor) to 5 (Exceptional)."),
        ("comment", "TEXT", "NOT NULL", "Detailed text review detailing trail conditions, guides, and meals.")
    ]
    for el in render_entity_table("ENTITY 7: REVIEWS", "Verified Trekker Experience Ratings & Testimonials", colors.HexColor("#EA580C"), reviews_rows):
        story.append(el)

    # =========================================================
    # PAGE 5: RELATIONSHIP MATRIX, VIEWS & PERFORMANCE
    # =========================================================
    story.append(PageBreak())

    story.append(Paragraph("6. Relationship Cardinality & Referential Integrity Matrix", section_heading))
    story.append(Paragraph(
        "Referential integrity constraints prevent dangling foreign keys and dictate cascading lifecycle rules across entities.",
        body_style
    ))

    rel_matrix_data = [
        [
            Paragraph("Primary (Parent)", table_header),
            Paragraph("Foreign (Child)", table_header),
            Paragraph("Foreign Key Column", table_header),
            Paragraph("Type", table_header),
            Paragraph("On Delete", table_header),
            Paragraph("Relational Meaning", table_header)
        ],
        [
            Paragraph("<b>USERS</b>", table_cell), Paragraph("<b>TREKS</b>", table_cell),
            Paragraph("assigned_staff_id", table_cell), Paragraph("1 : N", table_cell_bold),
            Paragraph("SET NULL", table_cell), Paragraph("One staff guide leads multiple expeditions.", table_cell)
        ],
        [
            Paragraph("<b>USERS</b>", table_cell), Paragraph("<b>BOOKINGS</b>", table_cell),
            Paragraph("user_id", table_cell), Paragraph("1 : N", table_cell_bold),
            Paragraph("RESTRICT", table_cell), Paragraph("User places bookings. User deletion restricted while bookings exist.", table_cell)
        ],
        [
            Paragraph("<b>TREKS</b>", table_cell), Paragraph("<b>BOOKINGS</b>", table_cell),
            Paragraph("trek_id", table_cell), Paragraph("1 : N", table_cell_bold),
            Paragraph("CASCADE", table_cell), Paragraph("An expedition receives multiple bookings from different trekkers.", table_cell)
        ],
        [
            Paragraph("<b>BOOKINGS</b>", table_cell), Paragraph("<b>TRANSACTIONS</b>", table_cell),
            Paragraph("booking_id", table_cell), Paragraph("1 : 1", table_cell_bold),
            Paragraph("CASCADE", table_cell), Paragraph("Each confirmed booking generates exactly one financial transaction record.", table_cell)
        ],
        [
            Paragraph("<b>TREKS</b>", table_cell), Paragraph("<b>SHOPS</b>", table_cell),
            Paragraph("trek_id", table_cell), Paragraph("1 : N", table_cell_bold),
            Paragraph("CASCADE", table_cell), Paragraph("An expedition route features multiple nearby gear rental shops.", table_cell)
        ],
        [
            Paragraph("<b>USERS</b>", table_cell), Paragraph("<b>RESCUE_OPS</b>", table_cell),
            Paragraph("trekker_id", table_cell), Paragraph("1 : N", table_cell_bold),
            Paragraph("CASCADE", table_cell), Paragraph("A trekker in distress broadcasts emergency SOS dispatch operations.", table_cell)
        ],
        [
            Paragraph("<b>USERS</b>", table_cell), Paragraph("<b>RESCUE_OPS</b>", table_cell),
            Paragraph("staff_id", table_cell), Paragraph("1 : N", table_cell_bold),
            Paragraph("SET NULL", table_cell), Paragraph("A staff guide is dispatched to coordinate rescue operations.", table_cell)
        ],
        [
            Paragraph("<b>TREKS</b>", table_cell), Paragraph("<b>RESCUE_OPS</b>", table_cell),
            Paragraph("trek_id", table_cell), Paragraph("1 : N", table_cell_bold),
            Paragraph("SET NULL", table_cell), Paragraph("A rescue occurs along a specific expedition trail or landmark.", table_cell)
        ],
        [
            Paragraph("<b>USERS</b>", table_cell), Paragraph("<b>REVIEWS</b>", table_cell),
            Paragraph("user_id", table_cell), Paragraph("1 : N", table_cell_bold),
            Paragraph("CASCADE", table_cell), Paragraph("Trekkers write verified reviews for completed expeditions.", table_cell)
        ],
        [
            Paragraph("<b>TREKS</b>", table_cell), Paragraph("<b>REVIEWS</b>", table_cell),
            Paragraph("trek_id", table_cell), Paragraph("1 : N", table_cell_bold),
            Paragraph("CASCADE", table_cell), Paragraph("Treks aggregate multiple 1 to 5 star ratings and feedback.", table_cell)
        ]
    ]
    rel_table = Table(rel_matrix_data, colWidths=[65, 80, 100, 45, 65, 185])
    rel_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(rel_table)
    story.append(Spacer(1, 8))

    # Analytical Views Section
    story.append(Paragraph("7. Relational SQL Views (Analytical Layer)", section_heading))
    views_data = [
        [Paragraph("View Name", table_header), Paragraph("Underlying Source Tables", table_header), Paragraph("Business Purpose & SQL Joins", table_header)],
        [
            Paragraph("<b>v_trek_availability</b>", table_cell),
            Paragraph("treks, bookings, users, reviews", table_cell),
            Paragraph("Computes real-time booked participants via SUM(num_participants), live open slots (max_capacity - booked), guide name, and average star rating.", table_cell)
        ],
        [
            Paragraph("<b>v_booking_details</b>", table_cell),
            Paragraph("bookings, users, treks, transactions", table_cell),
            Paragraph("Denormalized reservation report joining trekker profile, emergency contacts, expedition destination, and gateway transaction IDs.", table_cell)
        ],
        [
            Paragraph("<b>v_rescue_dashboard</b>", table_cell),
            Paragraph("rescue_operations, users, treks", table_cell),
            Paragraph("Mission control dispatch log joining victim name, assigned guide name, mobile emergency contacts, and GPS distress coordinates.", table_cell)
        ],
        [
            Paragraph("<b>v_trek_reviews</b>", table_cell),
            Paragraph("reviews, users, treks", table_cell),
            Paragraph("Customer testimonials view linking review comments, star ratings, reviewer name, and associated expedition route.", table_cell)
        ]
    ]
    views_table = Table(views_data, colWidths=[120, 130, 290])
    views_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(views_table)
    story.append(Spacer(1, 8))

    # Indexing & Performance Section
    story.append(Paragraph("8. Performance Indexing Strategy", section_heading))
    story.append(Paragraph(
        "To guarantee sub-millisecond query execution across large expedition datasets, B-Tree indexes are applied on all foreign key joins and frequent search filters:<br/>"
        "• <code>idx_bookings_trek</code> & <code>idx_bookings_user</code>: Accelerate booking lookups by expedition or user.<br/>"
        "• <code>idx_treks_staff</code>, <code>idx_treks_trending</code>, <code>idx_treks_category</code>: Fast landing page filtering.<br/>"
        "• <code>idx_rescue_trekker</code> & <code>idx_rescue_staff</code>: Real-time mission control SOS dispatch queries.<br/>"
        "• <code>idx_shops_trek</code> & <code>idx_reviews_trek</code>: Instant catalog joins on expedition detail views.",
        body_style
    ))

    # Build document
    doc.build(story, canvasmaker=PageDecoratedCanvas)
    print(f"[OK] Full ER Model PDF successfully generated at: {pdf_output_path}")
    return pdf_output_path


if __name__ == "__main__":
    png_path = generate_er_diagram_image("er_diagram.png")
    pdf_path = build_er_model_pdf(png_path, "Trekking_Management_System_ER_Model.pdf")
    print("Done generating ER diagram and PDF.")
