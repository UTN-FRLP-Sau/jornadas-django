import os
import time
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from charlas.models import Certificate


class Command(BaseCommand):
    help = 'Borra del disco los PDFs de certificados con más de N horas (default: 24). El PDF se regenera on-demand cuando el alumno descarga.'

    def add_arguments(self, parser):
        parser.add_argument('--horas', type=float, default=24.0,
                            help='Umbral de antigüedad en horas (default: 24)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Solo muestra qué se borraría, sin hacer cambios')

    def handle(self, *args, **options):
        umbral_segundos = options['horas'] * 3600
        ahora = time.time()
        dry_run = options['dry_run']

        certs = Certificate.objects.exclude(archivo='').exclude(archivo__isnull=True)
        borrados = 0
        errores = 0

        for cert in certs:
            try:
                path = Path(settings.MEDIA_ROOT) / cert.archivo.name
            except Exception:
                continue

            if not path.exists():
                # Archivo ya no existe; limpiar el campo
                if not dry_run:
                    cert.archivo = ''
                    cert.save(update_fields=['archivo'])
                continue

            edad = ahora - path.stat().st_mtime
            if edad < umbral_segundos:
                continue

            if dry_run:
                self.stdout.write(f'  [DRY] {path.name}  ({edad/3600:.1f}h)')
                borrados += 1
                continue

            try:
                os.remove(path)
                cert.archivo = ''
                cert.save(update_fields=['archivo'])
                borrados += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error borrando {path.name}: {e}'))
                errores += 1

        accion = 'Se borrarían' if dry_run else 'Borrados'
        self.stdout.write(self.style.SUCCESS(
            f'{accion}: {borrados} PDFs  |  Errores: {errores}'))
