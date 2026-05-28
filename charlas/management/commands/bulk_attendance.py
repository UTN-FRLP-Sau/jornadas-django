# charlas/management/commands/bulk_attendance.py
import csv
from django.core.management.base import BaseCommand
from charlas.models import Registration

'''
python manage.py bulk_attendance asistencias.csv
python manage.py bulk_attendance asistencias.csv --output resultado.csv
'''


class Command(BaseCommand):
    help = 'Carga masiva de asistencia desde CSV con columnas documento;charla'

    def add_arguments(self, parser):
        parser.add_argument('input_csv', type=str,
                            help='Ruta al CSV de entrada')
        parser.add_argument('--output', type=str,
                            help='Ruta al CSV de salida (opcional)')

    def handle(self, *args, **options):
        input_path = options['input_csv']
        output_path = options.get('output') or input_path.replace(
            '.csv', '_resultado.csv')

        results = []

        with open(input_path, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                dni = row.get('documento', '').strip()
                talk_id = row.get('charla', '').strip()

                try:
                    reg = Registration.objects.get(dni=dni, talk_id=talk_id)
                    reg.attended = True
                    reg.save()
                    estado = 'presente'
                except Registration.DoesNotExist:
                    estado = 'error'
                except Exception as e:
                    estado = f'error: {str(e)[:30]}'

                results.append({
                    'documento': dni,
                    'charla': talk_id,
                    'estado': estado,
                })

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f, fieldnames=['documento', 'charla', 'estado'], delimiter=';')
            writer.writeheader()
            writer.writerows(results)

        presentes = sum(1 for r in results if r['estado'] == 'presente')
        errores = sum(1 for r in results if r['estado'] != 'presente')

        self.stdout.write(self.style.SUCCESS(
            f'Procesados: {len(results)} | Presentes: {presentes} | Errores: {errores}'
        ))
        self.stdout.write(f'Resultado en: {output_path}')
