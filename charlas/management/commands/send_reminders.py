from PIL import Image, ImageDraw, ImageFont
import textwrap
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import get_connection
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import date, timedelta
from io import BytesIO
from itertools import groupby
import qrcode
from PIL import Image, ImageDraw
from charlas.models import Registration
from django.template.loader import render_to_string
import logging

logger = logging.getLogger('send_reminders')

'''
0 20 18,19,20 5 * cd /jornadas-django && .venv/bin/python manage.py send_reminders
'''

FONT_PATH = settings.BASE_DIR / 'charlas' / 'static' / 'charlas' / 'fonts' / 'Planc-Bold.otf'
TEMPLATE_PATH = settings.BASE_DIR / 'charlas' / 'static' / 'charlas' / 'img' / 'template_entrada.png'

FECHA_MAP = {
    date(2026, 5, 19): 'Martes 19 de Mayo',
    date(2026, 5, 20): 'Miércoles 20 de Mayo',
    date(2026, 5, 21): 'Jueves 21 de Mayo',
}

DEPT_COLORS = {
    'Magistral':  "#000000",
    'Básicas':    "#9A9B9C",
    'Civil':      '#0e8341',
    'Industrial': '#c05029',
    'Sistemas':   '#267e7c',
    'Química':    '#926d29',
    'Eléctrica':  "#cc3e45",
    'Mecánica':   '#2C3E50',
}


def _hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _build_qr_content(registration):
    return f"{registration.apellido}|{registration.legajo}|{registration.dni}|{registration.talk_id}|{registration.token}"


FONT_PATH = settings.BASE_DIR / 'charlas' / \
    'static' / 'charlas' / 'fonts' / 'Planc-Bold.otf'
TEMPLATE_PATH = settings.BASE_DIR / 'charlas' / \
    'static' / 'charlas' / 'img' / 'template_entrada.png'


def _ajustar_texto(texto, box_width, box_height, font_size):
    try:
        font = ImageFont.truetype(str(FONT_PATH), font_size)
    except:
        font = ImageFont.load_default(size=font_size)

    wrap_width = 30
    lines = textwrap.wrap(texto, width=wrap_width)

    total_height = sum(
        [font.getbbox(l)[3] - font.getbbox(l)[1] + 10 for l in lines])
    max_line_width = max(
        [font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines])

    while (total_height > box_height or max_line_width > box_width) and wrap_width > 10:
        wrap_width -= 1
        lines = textwrap.wrap(texto, width=wrap_width)
        total_height = sum(
            [font.getbbox(l)[3] - font.getbbox(l)[1] + 10 for l in lines])
        max_line_width = max(
            [font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines])

    return lines, font

def _ajustar_texto(texto, box_width, box_height, font_size):
    try:
        font = ImageFont.truetype(str(FONT_PATH), font_size)
    except:
        font = ImageFont.load_default(size=font_size)

    wrap_width = 30
    lines = textwrap.wrap(texto, width=wrap_width)

    total_height = sum(
        [font.getbbox(l)[3] - font.getbbox(l)[1] + 10 for l in lines])
    max_line_width = max(
        [font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines])

    while (total_height > box_height or max_line_width > box_width) and wrap_width > 10:
        wrap_width -= 1
        lines = textwrap.wrap(texto, width=wrap_width)
        total_height = sum(
            [font.getbbox(l)[3] - font.getbbox(l)[1] + 10 for l in lines])
        max_line_width = max(
            [font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines])

    return lines, font


def _generate_ticket(registration):
    talk = registration.talk
    img = Image.open(TEMPLATE_PATH).convert('RGB')
    draw = ImageDraw.Draw(img)
    width, height = img.size

    margin = int(width * 0.10)
    box_width = width - (margin * 2)
    y = int(height * 0.22)

    # Título de la charla
    lines, font_title = _ajustar_texto(
        talk.title, box_width, int(height * 0.15), int(width * 0.068)
    )
    for line in lines:
        bbox = font_title.getbbox(line)
        x = margin + (box_width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=font_title, fill=(44, 78, 254))
        y += bbox[3] - bbox[1] + 10
    y += int(height * 0.02)

    # Lugar y hora
    font_detail = ImageFont.truetype(str(FONT_PATH), int(width * 0.048))
    for texto in [f"Lugar: {talk.location or 'A confirmar'}", f"Hora: {talk.time}"]:
        try:
            bbox = font_detail.getbbox(texto)
        except:
            bbox = (0, 0, 100, 30)
        x = margin + (box_width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), texto, font=font_detail, fill=(51, 51, 51))
        y += int(height * 0.05)
    y += int(height * 0.02)

    # QR
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(_build_qr_content(registration))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white')
    if not isinstance(qr_img, Image.Image):
        qr_img = qr_img.get_image()
    qr_size = int(width * 0.55)
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    qr_x = (width - qr_size) // 2
    img.paste(qr_img, (qr_x, y))
    y += qr_size + int(height * 0.03)

    # Banda de departamento
    color = _hex_to_rgb(DEPT_COLORS.get(talk.department, '#2b4efe'))
    band_height = int(height * 0.05)
    band_rect = [margin, y, width - margin, y + band_height]
    draw.rounded_rectangle(band_rect, radius=15, fill=color)

    font_dept = ImageFont.truetype(str(FONT_PATH), int(width * 0.042))
    bbox = font_dept.getbbox(talk.department)
    text_x = (width - (bbox[2] - bbox[0])) // 2
    text_y = y + (band_height - (bbox[3] - bbox[1])) // 2

    out = BytesIO()
    img.save(out, format='PNG')
    return out.getvalue()


def _send_reminder(correo, nombre, registrations, fecha_str):

    html_body = render_to_string('charlas/email_recordatorio.html', {
        'nombre': nombre,
        'inscripciones': registrations,
        'fecha': fecha_str,
    })

    msg = MIMEMultipart('mixed')
    msg['Subject'] = 'Recordatorio — Jornadas de Formación Profesional'
    msg['From'] = settings.DEFAULT_FROM_EMAIL
    msg['To'] = correo

    alt = MIMEMultipart('alternative')
    alt.attach(MIMEText(html_body, 'html'))
    msg.attach(alt)

    for reg in registrations:
        ticket_bytes = _generate_ticket(reg)
        img_mime = MIMEImage(ticket_bytes)
        img_mime.add_header(
            'Content-Disposition', 'attachment',
            filename=f"entrada_{reg.talk.title[:30].replace(' ', '_')}.png"
        )
        msg.attach(img_mime)

    try:
        connection = get_connection()
        connection.open()
        connection.connection.sendmail(
            settings.DEFAULT_FROM_EMAIL,
            [correo],
            msg.as_string()
        )
        connection.close()
        return True
    except Exception as exc:
        print(f'[EMAIL] Error enviando a {correo}: {exc}')
        return False


class Command(BaseCommand):
    help = 'Envía recordatorios con entradas QR a inscriptos del día siguiente.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha a procesar en formato DD-MM-YYYY (para testing)',
        )

    def handle(self, *args, **kwargs):
        if kwargs.get('fecha'):
            from datetime import datetime
            tomorrow = datetime.strptime(kwargs['fecha'], '%d-%m-%Y').date()
        else:
            tomorrow = date.today() + timedelta(days=1)
        fecha_str = FECHA_MAP.get(tomorrow)

        if not fecha_str:
            self.stdout.write(self.style.WARNING(
                'No hay charlas programadas para mañana.'))
            return

        regs = (
            Registration.objects
            # "19", "20", "21"
            .filter(talk__date__icontains=fecha_str.split(' ')[1])
            .select_related('talk')
            .order_by('correo')
        )

        if not regs.exists():
            self.stdout.write(self.style.WARNING(
                f'Sin inscriptos para {fecha_str}.'))
            return

        enviados = 0
        errores = 0
        for correo, grupo in groupby(regs, key=lambda r: r.correo):
            inscripciones = list(grupo)
            nombre = inscripciones[0].nombre
            ok = _send_reminder(correo, nombre, inscripciones, fecha_str)
            charlas_str = ', '.join([r.talk.title for r in inscripciones])
            if ok:
                enviados += 1
                logger.info(
                    f"OK | {correo} | {len(inscripciones)} charla/s | {charlas_str}")
                self.stdout.write(self.style.SUCCESS(
                    f'  ✔ {correo} ({len(inscripciones)} charla/s)'))
            else:
                errores += 1
                logger.error(
                    f"ERROR | {correo} | {len(inscripciones)} charla/s | {charlas_str}")
                self.stdout.write(self.style.ERROR(f'  ✗ {correo}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nEnviados: {enviados} | Errores: {errores}'))
