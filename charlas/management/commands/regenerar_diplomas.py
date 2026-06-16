# charlas/management/commands/regenerar_diplomas.py
import os
import time
import threading
from django.core.management.base import BaseCommand
from django.conf import settings
from charlas.models import Certificate
from charlas.views import _generate_certificate_pdf, _send_certificate_email
from django.template.loader import render_to_string
from django.core.mail import get_connection
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _send_fe_erratas(cert):
    try:
        from django.core.mail import get_connection
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        html = render_to_string('charlas/email_fe_erratas.html', {
            'cert': cert,
            'site_url': settings.SITE_URL,
        })

        msg = MIMEMultipart('mixed')
        msg['Subject'] = 'Corrección de certificado — Jornadas de Formación Profesional 2026'
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = cert.correo

        alt = MIMEMultipart('alternative')
        alt.attach(MIMEText(html, 'html'))
        msg.attach(alt)

        # Adjuntar PDF
        if cert.archivo:
            pdf_path = settings.MEDIA_ROOT / cert.archivo.name
            if pdf_path.exists():
                with open(pdf_path, 'rb') as f:
                    pdf = MIMEApplication(f.read(), _subtype='pdf')
                    pdf.add_header(
                        'Content-Disposition', 'attachment',
                        filename=f'diploma_{cert.apellido}_{cert.nombre}.pdf'
                    )
                    msg.attach(pdf)

        connection = get_connection()
        connection.open()
        connection.connection.sendmail(
            settings.DEFAULT_FROM_EMAIL,
            [cert.correo],
            msg.as_string()
        )
        connection.close()
        return True
    except Exception as e:
        print(f'[FE ERRATAS] Error enviando a {cert.correo}: {e}')
        return False


def _run_en_background(certs, tanda_size, espera_horas, solo_descargados):
    tandas = [certs[i:i+tanda_size] for i in range(0, len(certs), tanda_size)]

    for i, tanda in enumerate(tandas):
        print(
            f'[TANDA {i+1}/{len(tandas)}] Procesando {len(tanda)} certificados...')

        for cert in tanda:
            # Borrar PDF viejo
            if cert.archivo:
                path = settings.MEDIA_ROOT / cert.archivo.name
                if path.exists():
                    os.remove(path)
            cert.archivo = ''
            cert.save()

            # Regenerar
            try:
                archivo = _generate_certificate_pdf(cert)
                cert.archivo = archivo
                cert.save()
            except Exception as e:
                print(f'[ERROR] Generando {cert.dni}: {e}')
                continue

            # Enviar fe de erratas si descargó
            if not solo_descargados or cert.fue_descargado:
                ok = _send_fe_erratas(cert)
                print(
                    f'  {"✔" if ok else "✗"} {cert.apellido}, {cert.nombre} — {cert.correo}')

        if i < len(tandas) - 1:
            print(
                f'[TANDA {i+1}] Esperando {espera_horas}h para la próxima tanda...')
            time.sleep(espera_horas * 3600)

    print('[DONE] Regeneración y envío completados.')


class Command(BaseCommand):
    help = 'Regenera diplomas con template correcto y envía fe de erratas en tandas'

    def add_arguments(self, parser):
        parser.add_argument('--tanda', type=int, default=500,
                            help='Tamaño de cada tanda (default: 500)')
        parser.add_argument('--espera', type=float, default=1.0,
                            help='Horas entre tandas (default: 1)')
        parser.add_argument('--solo-descargados', action='store_true',
                            help='Solo enviar correo a quienes descargaron')
        parser.add_argument('--dry-run', action='store_true',
                            help='Simular sin hacer cambios')

    def handle(self, *args, **options):
        certs = list(Certificate.objects.filter(tipo='diploma'))
        self.stdout.write(f'Certificados a regenerar: {len(certs)}')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(
                'DRY RUN — no se hacen cambios.'))
            for cert in certs[:10]:
                self.stdout.write(
                    f'  {cert.apellido}, {cert.nombre} — {cert.correo}')
            return

        self.stdout.write(
            f'Tanda: {options["tanda"]} | Espera: {options["espera"]}h')
        self.stdout.write('Iniciando en segundo plano...')

        t = threading.Thread(
            target=_run_en_background,
            args=(certs, options['tanda'], options['espera'],
                  options['solo_descargados']),
            daemon=True
        )
        t.start()

        self.stdout.write(self.style.SUCCESS(
            'Proceso iniciado. Revisá los logs para seguimiento.'))
        t.join()
