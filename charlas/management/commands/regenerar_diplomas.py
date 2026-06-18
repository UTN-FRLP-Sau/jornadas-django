# charlas/management/commands/regenerar_diplomas.py
import os
import time
import threading
from django.core.management.base import BaseCommand
from django.conf import settings
from charlas.models import Certificate, generate_cert_code
from charlas.views import _generate_certificate_pdf
from django.template.loader import render_to_string
from django.core.mail import get_connection
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _build_message(cert, attach_pdf=False):
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

    if attach_pdf and cert.archivo:
        pdf_path = settings.MEDIA_ROOT / cert.archivo.name
        if pdf_path.exists():
            with open(pdf_path, 'rb') as f:
                pdf = MIMEApplication(f.read(), _subtype='pdf')
                pdf.add_header(
                    'Content-Disposition', 'attachment',
                    filename=f'diploma_{cert.apellido}_{cert.nombre}.pdf'
                )
                msg.attach(pdf)

    return msg


def _send_fe_erratas(cert, attach_pdf=False, connection=None):
    try:
        msg = _build_message(cert, attach_pdf)
        if connection:
            connection.connection.sendmail(
                settings.DEFAULT_FROM_EMAIL, [cert.correo], msg.as_string()
            )
        else:
            conn = get_connection()
            conn.open()
            conn.connection.sendmail(
                settings.DEFAULT_FROM_EMAIL, [cert.correo], msg.as_string()
            )
            conn.close()
        return True
    except Exception as e:
        print(f'[FE ERRATAS] Error enviando a {cert.correo}: {e}')
        return False


def _run_en_background(certs, tanda_size, espera_horas, job_id):
    from django.utils import timezone
    from charlas.models import Survey, EmissionJob

    job = EmissionJob.objects.get(id=job_id)
    job.status = 'procesando'
    job.save()

    dnis_con_encuesta = set(
        Survey.objects.filter(completada=True).values_list('certificate__dni', flat=True)
    )
    print(f'[INFO] {len(dnis_con_encuesta)} alumnos con encuesta completada recibirán el diploma adjunto.')

    tandas = [certs[i:i+tanda_size] for i in range(0, len(certs), tanda_size)]

    try:
        for i, tanda in enumerate(tandas):
            print(f'[TANDA {i+1}/{len(tandas)}] Procesando {len(tanda)} certificados...')

            # Una sola conexión SMTP por tanda (evita múltiples DNS lookups)
            conn = get_connection()
            conn.open()

            for cert in tanda:
                # Borrar PDF viejo
                if cert.archivo:
                    path = settings.MEDIA_ROOT / cert.archivo.name
                    if path.exists():
                        os.remove(path)
                cert.archivo = ''

                # Cambiar código de validación (invalida el diploma anterior)
                cert.codigo = generate_cert_code()
                cert.save()

                # Regenerar PDF con el nuevo código
                try:
                    archivo = _generate_certificate_pdf(cert)
                    cert.archivo = archivo
                    cert.save()
                except Exception as e:
                    print(f'[ERROR] Generando {cert.dni}: {e}')
                    job.errores += 1
                    job.save()
                    continue

                # Enviar fe de erratas a todos; adjuntar PDF solo a quienes completaron la encuesta
                attach_pdf = cert.dni in dnis_con_encuesta
                ok = _send_fe_erratas(cert, attach_pdf=attach_pdf, connection=conn)
                adjunto_str = ' [+diploma]' if attach_pdf else ''
                print(f'  {"✔" if ok else "✗"} {cert.apellido}, {cert.nombre} — {cert.correo}{adjunto_str}')

                if ok:
                    job.enviados += 1
                else:
                    job.errores += 1
                job.save()

                time.sleep(3)

            conn.close()

            if i < len(tandas) - 1:
                print(f'[TANDA {i+1}] Esperando {espera_horas}h para la próxima tanda...')
                time.sleep(espera_horas * 3600)

        job.status = 'completado'
        job.finished_at = timezone.now()
        job.save()
        print('[DONE] Regeneración y envío completados.')

    except Exception as e:
        job.status = 'error'
        job.finished_at = timezone.now()
        job.save()
        print(f'[FATAL] {e}')


class Command(BaseCommand):
    help = 'Regenera diplomas con nuevo código (invalida anteriores) y envía fe de erratas. Adjunta el diploma a quienes completaron la encuesta.'

    def add_arguments(self, parser):
        parser.add_argument('--tanda', type=int, default=500,
                            help='Tamaño de cada tanda (default: 500)')
        parser.add_argument('--espera', type=float, default=1.0,
                            help='Horas entre tandas (default: 1)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Simular sin hacer cambios')
        parser.add_argument('--test-email', type=str,
                            help='Enviar solo el primer certificado a este correo para prueba')

    def handle(self, *args, **options):
        from charlas.models import Survey

        certs = list(Certificate.objects.filter(tipo='diploma'))
        con_encuesta = Survey.objects.filter(completada=True).count()
        self.stdout.write(f'Diplomas a procesar: {len(certs)}')
        self.stdout.write(f'Con encuesta completada (recibirán PDF adjunto): {con_encuesta}')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN — no se hacen cambios.'))
            for cert in certs[:10]:
                has_survey = Survey.objects.filter(certificate=cert, completada=True).exists()
                self.stdout.write(
                    f'  {cert.apellido}, {cert.nombre} — {cert.correo}'
                    f'{" [+diploma]" if has_survey else ""}')
            return

        if options.get('test_email'):
            from charlas.models import Survey
            destino = options['test_email']

            # Buscar un cert con encuesta y uno sin, para probar ambas versiones
            cert_con = (
                Certificate.objects.filter(tipo='diploma', survey__completada=True).first()
                or Certificate.objects.filter(tipo='diploma').first()
            )
            cert_sin = (
                Certificate.objects.filter(tipo='diploma').exclude(survey__completada=True).first()
                or cert_con
            )

            for cert, con_adjunto, label in [
                (cert_sin, False, 'SIN adjunto'),
                (cert_con, True, 'CON adjunto'),
            ]:
                if not cert:
                    self.stdout.write(self.style.WARNING(f'No hay cert para prueba {label}'))
                    continue

                # Regenerar PDF con el template actual (sin cambiar código ni guardar en DB)
                try:
                    archivo = _generate_certificate_pdf(cert)
                    cert.archivo = archivo
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'[{label}] Error generando PDF: {e}'))
                    continue

                cert.correo = destino  # override en memoria, sin guardar
                ok = _send_fe_erratas(cert, attach_pdf=con_adjunto)
                estado = self.style.SUCCESS('OK') if ok else self.style.ERROR('ERROR')
                self.stdout.write(f'[{label}] → {destino}: {estado}')
            return

        from charlas.models import EmissionJob

        job = EmissionJob.objects.create(total=len(certs))
        self.stdout.write(f'Tanda: {options["tanda"]} | Espera: {options["espera"]}h')
        self.stdout.write(self.style.SUCCESS(
            f'Seguimiento en: {settings.SITE_URL}/admin/certificados/emitir/{job.id}/'))
        self.stdout.write('Iniciando en segundo plano...')

        t = threading.Thread(
            target=_run_en_background,
            args=(certs, options['tanda'], options['espera'], job.id),
            daemon=True
        )
        t.start()

        self.stdout.write(self.style.SUCCESS('Proceso iniciado. Revisá los logs para seguimiento.'))
        t.join()
