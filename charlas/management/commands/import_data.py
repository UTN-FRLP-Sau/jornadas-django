from django.core.management.base import BaseCommand
import json
from charlas.models import Talk, Registration


class Command(BaseCommand):
    help = 'Importa charlas e inscriptos desde JSON exportado del servidor.'

    def add_arguments(self, parser):
        parser.add_argument('json_path', type=str)

    def handle(self, *args, **options):
        with open(options['json_path'], encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            t = item['talk']
            talk, created = Talk.objects.get_or_create(
                title=t['title'],
                date=t['date'],
                defaults={
                    'time': t['time'],
                    'department': t['department'],
                    'location': t.get('location', ''),
                    'capacity': t['capacity'],
                    'target_year': t['target_year'],
                    'speaker': t['speaker'],
                    'description': t['description'],
                }
            )
            self.stdout.write(
                f"{'Creada' if created else 'Existente'}: {talk.title} (ID {talk.id})")

            created_regs = 0
            for r in item['registrations']:
                reg, was_created = Registration.objects.get_or_create(
                    token=r['token'],
                    defaults={
                        'talk': talk,
                        'nombre': r['nombre'],
                        'apellido': r['apellido'],
                        'dni': r['dni'],
                        'legajo': r['legajo'],
                        'correo': r['correo'],
                        'attended': r['attended'],
                    }
                )
                if was_created:
                    created_regs += 1

            self.stdout.write(
                f"  Inscriptos creados: {created_regs} / {len(item['registrations'])}")
