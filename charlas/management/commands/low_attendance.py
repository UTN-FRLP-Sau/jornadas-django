# charlas/management/commands/low_attendance.py
from django.core.management.base import BaseCommand
from charlas.models import Talk

class Command(BaseCommand):
    help = 'Lista charlas con menos de X% de asistencia'

    def add_arguments(self, parser):
        parser.add_argument('porcentaje', type=float,
                            help='Porcentaje máximo (ej: 50)')

    def handle(self, *args, **options):
        umbral = options['porcentaje']
        self.stdout.write(
            f"\nCharlas con menos del {umbral}% de asistencia:\n")
        self.stdout.write('-' * 100)
        self.stdout.write(
            f"{'Charla':<50} {'Depto':<12} {'Inscriptos':>10} {'Presentes':>10} {'%':>8}")
        self.stdout.write('-' * 100)

        encontradas = 0
        for talk in Talk.objects.all().order_by('department', 'date'):
            i = talk.registered_count
            p = talk.registrations.filter(attended=True).count()
            pct = round(p / i * 100, 1) if i > 0 else 0
            if pct < umbral:
                self.stdout.write(
                    f"{talk.title[:48]:<50} {talk.department[:10]:<12} {i:>10} {p:>10} {pct:>7}%"
                )
                encontradas += 1

        self.stdout.write('-' * 100)
        self.stdout.write(self.style.SUCCESS(
            f"\nTotal: {encontradas} charlas bajo el {umbral}%"))
