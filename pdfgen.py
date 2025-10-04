from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.units import inch
import numpy as np
from io import BytesIO

def draw_swatch(c, x, y, w, h, hex_color, label):
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.setFillColor(colors.HexColor(hex_color))
    c.rect(x, y, w, h, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.drawString(x, y - 12, label)

def np_to_reader(arr):
    bio = BytesIO()
    from PIL import Image
    Image.fromarray(arr).save(bio, format="JPEG", quality=90)
    bio.seek(0)
    return ImageReader(bio)

def build_paint_plan_pdf(pdf_path, original: np.ndarray, preview: np.ndarray, brand: str, wall_hex: str, trim_hex: str):
    c = canvas.Canvas(pdf_path, pagesize=letter)
    W, H = letter
    margin = 36

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, H - margin, "Paint Plan")
    c.setFont("Helvetica", 10)
    c.drawString(margin, H - margin - 16, "Colors are approximations. Confirm with a physical sample.")

    # Images
    img_w = (W - margin*3) / 2
    img_h = img_w * 0.66
    c.drawString(margin, H - margin - 40, "Original")
    c.drawImage(np_to_reader(original), margin, H - margin - 40 - img_h, width=img_w, height=img_h, preserveAspectRatio=True, anchor='sw')
    c.drawString(margin*2 + img_w, H - margin - 40, "Preview")
    c.drawImage(np_to_reader(preview), margin*2 + img_w, H - margin - 40 - img_h, width=img_w, height=img_h, preserveAspectRatio=True, anchor='sw')

    # Swatches
    sw_y = H - margin - 60 - img_h - 10
    draw_swatch(c, margin, sw_y, 60, 30, wall_hex, f"Wall: {wall_hex} ({brand})")
    draw_swatch(c, margin+70, sw_y, 60, 30, trim_hex, f"Trim: {trim_hex}")

    # Shopping list (placeholder)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, sw_y - 24, "DIY Shopping List")
    c.setFont("Helvetica", 10)
    y = sw_y - 40
    items = [
        ("Roller Kit", "Paid link: we may earn a commission"),
        ("Painter's Tape", ""),
        ("Drop Cloth", ""),
        ("Sample Pot(s)", ""),
    ]
    for name, note in items:
        c.drawString(margin, y, f"• {name} {('— '+note) if note else ''}")
        y -= 14

    # CTA
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y - 10, "Ready to skip the mess? Book a professional paint consult:")
    c.setFont("Helvetica", 10)
    c.drawString(margin, y - 26, "Visit: yoursite.com/book  |  Call: (555) 555-0123")

    # Footer
    c.setFont("Helvetica", 8)
    c.drawRightString(W - margin, margin, "© Your Painting Co. | Visuals are illustrative; actual results depend on lighting and surface prep.")
    c.showPage()
    c.save()
