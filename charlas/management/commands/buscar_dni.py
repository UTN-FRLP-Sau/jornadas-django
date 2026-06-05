# charlas/management/commands/buscar_dni.py
from django.core.management.base import BaseCommand
from charlas.models import Registration


class Command(BaseCommand):
    help = 'Busca un DNI en todas las inscripciones y muestra sus datos'

    def add_arguments(self, parser):
        parser.add_argument('dni', type=str, nargs='+', help='DNI/s a buscar')
        parser.add_argument('--list', action='store_true',
                            help='Exportar en formato CSV')

    def handle(self, *args, **options):
        for dni in options['dni']:
            dni = dni.strip()
            regs = Registration.objects.filter(dni=dni).select_related(
                'talk').order_by('talk__date', 'talk__time')

            if not regs.exists():
                self.stdout.write(self.style.ERROR(
                    f'\nNo se encontraron inscripciones para el DNI {dni}'))
                continue

            reg = regs.first()

            if options['list']:
                self.stdout.write(
                    f"{reg.dni};{reg.legajo};{reg.nombre};{reg.apellido};{reg.correo}"
                )
                continue

            self.stdout.write(f"\nDatos del alumno:")
            self.stdout.write(f"  Nombre:  {reg.apellido}, {reg.nombre}")
            self.stdout.write(f"  DNI:     {reg.dni}")
            self.stdout.write(f"  Legajo:  {reg.legajo}")
            self.stdout.write(f"  Correo:  {reg.correo}")

            self.stdout.write(f"\nInscripciones ({regs.count()}):")
            self.stdout.write('-' * 90)
            self.stdout.write(
                f"{'ID':>5} {'Charla':<45} {'Depto':<12} {'Fecha':<22} {'Presente':>10}")
            self.stdout.write('-' * 90)

            for r in regs:
                presente = '✔' if r.attended else '✗'
                reclamo = ' (reclamo)' if r.attended_reclamo else ''
                self.stdout.write(
                    f"{r.talk.id:>5} {r.talk.title[:43]:<45} {r.talk.department[:10]:<12} {r.talk.date:<22} {presente + reclamo:>10}"
                )

            self.stdout.write('-' * 90 + '\n')
