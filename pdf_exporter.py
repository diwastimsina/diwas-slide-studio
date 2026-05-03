"""
Exports the slide deck to PDF by rendering each slide thumbnail into a PDF page.
Uses reportlab so no LibreOffice dependency needed.
"""

import io
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from preview_renderer import render_slide_thumbnail

PAGE_W, PAGE_H = landscape(A4)  # 841 x 595 pts


def build_pdf(analysis: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    theme = analysis.get("theme", "professional")
    slides = analysis.get("slides", [])

    for slide in slides:
        thumb_bytes = render_slide_thumbnail(slide, theme)
        img = ImageReader(io.BytesIO(thumb_bytes))
        # Fill the full page with the slide image
        c.drawImage(img, 0, 0, PAGE_W, PAGE_H, preserveAspectRatio=False)
        c.showPage()

    c.save()
    buf.seek(0)
    return buf.getvalue()
