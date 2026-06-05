# charlas/management/commands/bulk_register.py
import csv
import uuid
from django.core.management.base import BaseCommand
from charlas.models import Talk, Registration


class Command(BaseCommand):
    help = 'Inscripción masiva desde CSV. Columnas: dni;legajo;nombre;apellido;correo;charla_id'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str,
                            help='Ruta al CSV de entrada')
        parser.add_argument('--output', type=str,
                            help='Ruta al CSV de salida (opcional)')
        parser.add_argument('--attended', action='store_true',
                            help='Marcar como presente automáticamente')

    def handle(self, *args, **options):
        input_path = options['csv_path']
        output_path = options.get('output') or input_path.replace(
            '.csv', '_resultado.csv')
        attended = options['attended']

        results = []
        creados = 0
        duplicados = 0
        errores = 0

        with open(input_path, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                dni = row.get('dni', '').strip()
                legajo = row.get('legajo', '').strip()
                nombre = row.get('nombre', '').strip()
                apellido = row.get('apellido', '').strip()
                correo = row.get('correo', '').strip()
                charla_id = row.get('charla_id', '').strip()

                try:
                    talk = Talk.objects.get(pk=charla_id)
                    reg, created = Registration.objects.get_or_create(
                        talk=talk,
                        dni=dni,
                        defaults={
                            'legajo': legajo,
                            'nombre': nombre,
                            'apellido': apellido,
                            'correo': correo,
                            'token': str(uuid.uuid4()),
                            'attended': attended,
                        }
                    )
                    if created:
                        estado = 'creado'
                        creados += 1
                    else:
                        estado = 'duplicado'
                        duplicados += 1
                except Talk.DoesNotExist:
                    estado = 'charla_no_encontrada'
                    errores += 1
                except Exception as e:
                    estado = f'error: {str(e)[:30]}'
                    errores += 1

                results.append({
                    'dni': dni,
                    'legajo': legajo,
                    'nombre': nombre,
                    'apellido': apellido,
                    'charla_id': charla_id,
                    'estado': estado,
                })

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f, fieldnames=['dni', 'legajo', 'nombre',
                               'apellido', 'charla_id', 'estado'],
                delimiter=';'
            )
            writer.writeheader()
            writer.writerows(results)

        self.stdout.write(self.style.SUCCESS(
            f'Creados: {creados} | Duplicados: {duplicados} | Errores: {errores}'
        ))
        self.stdout.write(f'Resultado en: {output_path}')
