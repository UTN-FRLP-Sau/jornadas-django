# generate_disertantes.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from pypdf import PdfReader, PdfWriter
from io import BytesIO
from pathlib import Path
import unicodedata
import re


def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode(
        'ascii', 'ignore').decode('ascii')
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

TEMPLATE_PATH = Path("media/JFP2026 CERTIFICADO DISERTANTE.pdf")
NOMBRES_PATH = Path("disertantes.txt")
OUTPUT_DIR = Path("media/disertantes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = landscape(A4)

nombres = [l.strip() for l in NOMBRES_PATH.read_text(
    encoding='utf-8').splitlines() if l.strip()]

for nombre in nombres:
    overlay_buffer = BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=landscape(A4))
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(W / 2, H / 2 + 10, nombre.upper())
    c.save()
    overlay_buffer.seek(0)

    template_pdf = PdfReader(str(TEMPLATE_PATH))
    overlay_pdf = PdfReader(overlay_buffer)
    writer = PdfWriter()
    page = template_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    filename = OUTPUT_DIR / f"{slugify(nombre)}.pdf"
    with open(filename, 'wb') as f:
        writer.write(f)
    print(f"✔ {nombre}")

print(f"\nGenerados en: {OUTPUT_DIR}")
