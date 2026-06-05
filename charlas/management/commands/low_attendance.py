# charlas/management/commands/low_attendance.py
from django.core.management.base import BaseCommand
from charlas.models import Talk, Registration


class Command(BaseCommand):
    help = 'Lista charlas con menos de X% de asistencia y permite marcar presentes en masa'

    def add_arguments(self, parser):
        parser.add_argument('porcentaje', type=float, help='Porcentaje máximo (ej: 50)')

    def handle(self, *args, **options):
        umbral = options['porcentaje']

        while True:
            self.stdout.write(f"\nCharlas con menos del {umbral}% de asistencia:\n")
            self.stdout.write('-' * 105)
            self.stdout.write(f"{'ID':>5} {'Charla':<48} {'Depto':<12} {'Inscriptos':>10} {'Presentes':>10} {'%':>8}")
            self.stdout.write('-' * 105)

            talks_mostradas = []
            for talk in Talk.objects.all().order_by('department', 'date'):
                i = talk.registered_count
                p = talk.registrations.filter(attended=True).count()
                pct = round(p / i * 100, 1) if i > 0 else 0
                if pct < umbral:
                    self.stdout.write(
                        f"{talk.id:>5} {talk.title[:46]:<48} {talk.department[:10]:<12} {i:>10} {p:>10} {pct:>7}%"
                    )
                    talks_mostradas.append(talk.id)

            self.stdout.write('-' * 105)
            self.stdout.write(f"\nTotal: {len(talks_mostradas)} charlas bajo el {umbral}%")
            self.stdout.write("\nIngresá el ID de una charla para marcar todos los inscriptos como presentes.")
            self.stdout.write("Escribí 'salir' para cerrar.\n")

            entrada = input(">> ").strip()

            if entrada.lower() == 'salir':
                self.stdout.write(self.style.SUCCESS("Saliendo..."))
                break

            if not entrada.isdigit():
                self.stdout.write(self.style.ERROR("ID inválido."))
                continue

            talk_id = int(entrada)
            if talk_id not in talks_mostradas:
                self.stdout.write(self.style.ERROR(f"ID {talk_id} no está en la lista."))
                continue

            try:
                talk = Talk.objects.get(pk=talk_id)
                actualizados = Registration.objects.filter(
                    talk=talk, attended=False
                ).update(attended=True)
                self.stdout.write(self.style.SUCCESS(
                    f"✔ {actualizados} inscriptos marcados como presentes en '{talk.title}'"
                ))
            except Talk.DoesNotExist:
                self.stdout.write(self.style.ERROR("Charla no encontrada."))