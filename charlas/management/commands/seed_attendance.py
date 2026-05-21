# charlas/management/commands/seed_attendance.py
from django.core.management.base import BaseCommand
from charlas.models import Talk, Registration
import uuid
import random

NOMBRES = ['Juan', 'María', 'Carlos', 'Ana', 'Pedro',
           'Laura', 'Diego', 'Sofía', 'Martín', 'Valentina']
APELLIDOS = ['García', 'López', 'Martínez', 'Rodríguez',
             'González', 'Pérez', 'Sánchez', 'Romero', 'Torres', 'Díaz']


class Command(BaseCommand):
    help = 'Seed de inscriptos y asistencia para testing del dashboard'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                            help='Eliminar inscripciones existentes antes del seed')

    def handle(self, *args, **options):
        if options['clear']:
            Registration.objects.all().delete()
            self.stdout.write(self.style.WARNING('Inscripciones eliminadas.'))

        talks = Talk.objects.all()
        if not talks.exists():
            self.stdout.write(self.style.ERROR(
                'No hay charlas. Corré el seed de charlas primero.'))
            return

        dni_counter = 30000000
        created = 0

        for talk in talks:
            n_inscriptos = random.randint(20, talk.capacity)
            attended_count = int(n_inscriptos * random.uniform(0.55, 0.95))

            for i in range(n_inscriptos):
                dni = str(dni_counter + i)
                if Registration.objects.filter(talk=talk, dni=dni).exists():
                    continue
                Registration.objects.create(
                    talk=talk,
                    nombre=random.choice(NOMBRES),
                    apellido=random.choice(APELLIDOS),
                    dni=dni,
                    legajo=str(random.randint(50000, 99999)),
                    correo=f'alumno{dni}@utn.edu.ar',
                    token=str(uuid.uuid4()),
                    attended=(i < attended_count),
                )
                created += 1
            dni_counter += n_inscriptos + 1
            self.stdout.write(self.style.SUCCESS(
                f'  ✔ {talk.title[:40]} — {n_inscriptos} inscriptos, {attended_count} presentes'))

        self.stdout.write(self.style.SUCCESS(f'\nTotal creados: {created}'))
