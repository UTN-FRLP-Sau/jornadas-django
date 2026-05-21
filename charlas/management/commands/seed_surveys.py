# charlas/management/commands/seed_surveys.py
from django.core.management.base import BaseCommand
from charlas.models import Certificate, Survey, TalkRating, Registration
import random

CARRERAS = ['Industrial', 'Sistemas',
            'Mecánica', 'Química', 'Civil', 'Eléctrica']
ANIOS = ['1°', '2°', '3°', '4°', '5°', '6°']
EVAL_GENERAL = ['Muy buenas', 'Buenas', 'Regulares', 'Malas', 'Muy malas']
APORTE = ['Mucho', 'Bastante', 'Poco', 'Nada']
INTERES = ['Muy interesantes', 'Interesantes',
           'Neutras', 'Poco interesantes', 'Nada interesantes']
MATRIZ_OPTS = ['Muy bueno', 'Bueno', 'Regular', 'Malo', 'Muy malo']
EVAL_FERIA = ['Muy buena', 'Buena', 'Regular', 'Mala', 'Muy mala']
UTILIDAD = ['Mucho', 'Bastante', 'Poco']
CONOCIO = ['Sí', 'No', 'En parte']

LO_MEJOR = [
    'Las charlas magistrales estuvieron muy buenas',
    'La variedad de temas fue excelente',
    'Los disertantes tenían mucha experiencia',
    'La organización fue muy buena este año',
    'La feria de empresas me ayudó a hacer contactos',
    'Las charlas de mi departamento fueron muy interesantes',
    'El nivel de los expositores fue alto',
    'La posibilidad de conocer profesionales del sector',
]

A_MEJORAR = [
    'Los horarios se superponían entre charlas',
    'Faltó más espacio para las charlas magistrales',
    'La comunicación previa podría mejorar',
    'El sistema de inscripción tuvo problemas',
    'Deberían dar más tiempo para preguntas',
    'Las aulas eran pequeñas para la cantidad de asistentes',
    'Mejorar la señalización del evento',
]

PROXIMA = [
    'Más charlas sobre inteligencia artificial',
    'Talleres prácticos además de charlas',
    'Más empresas en la feria',
    'Charlas sobre emprendimiento',
    'Más disertantes del exterior',
    'Transmisión online de las charlas magistrales',
]


class Command(BaseCommand):
    help = 'Seed de encuestas para testing del dashboard'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true')

    def handle(self, *args, **options):
        if options['clear']:
            Survey.objects.all().delete()
            self.stdout.write(self.style.WARNING('Encuestas eliminadas.'))

        certs = Certificate.objects.all()
        if not certs.exists():
            self.stdout.write(self.style.ERROR(
                'No hay certificados. Emití certificados primero.'))
            return

        created = 0
        for cert in certs:
            if Survey.objects.filter(certificate=cert).exists():
                continue

            asistio_empresas = random.choice([True, False])
            asistio_laboratorios = random.choice([True, False])

            survey = Survey.objects.create(
                certificate=cert,
                carrera=random.choice(CARRERAS),
                anio_cursada=random.choice(ANIOS),
                evaluacion_general=random.choices(
                    EVAL_GENERAL, weights=[40, 35, 15, 7, 3])[0],
                aporte_formacion=random.choices(
                    APORTE, weights=[40, 35, 20, 5])[0],
                interes_tematicas=random.choices(
                    INTERES, weights=[35, 40, 15, 7, 3])[0],
                organizacion_general=random.choices(
                    [1, 2, 3, 4, 5], weights=[3, 7, 15, 35, 40])[0],
                matriz_variedad=random.choices(
                    MATRIZ_OPTS, weights=[30, 40, 20, 7, 3])[0],
                matriz_disertantes=random.choices(
                    MATRIZ_OPTS, weights=[35, 40, 15, 7, 3])[0],
                matriz_horarios=random.choices(
                    MATRIZ_OPTS, weights=[20, 35, 30, 10, 5])[0],
                matriz_informacion=random.choices(
                    MATRIZ_OPTS, weights=[25, 35, 25, 10, 5])[0],
                matriz_inscripcion=random.choices(
                    MATRIZ_OPTS, weights=[30, 35, 20, 10, 5])[0],
                matriz_acreditacion=random.choices(
                    MATRIZ_OPTS, weights=[25, 35, 25, 10, 5])[0],
                matriz_espacios=random.choices(
                    MATRIZ_OPTS, weights=[20, 30, 30, 15, 5])[0],
                matriz_colaboradores=random.choices(
                    MATRIZ_OPTS, weights=[35, 40, 15, 7, 3])[0],
                lo_mejor=random.choice(LO_MEJOR),
                a_mejorar=random.choice(A_MEJORAR),
                asistio_feria_empresas=asistio_empresas,
                evaluacion_feria_empresas=random.choice(
                    EVAL_FERIA) if asistio_empresas else '',
                utilidad_feria_empresas=random.choice(
                    UTILIDAD) if asistio_empresas else '',
                stands_interesantes='TCS, Grupo Techint' if asistio_empresas else '',
                mejoras_feria_empresas=random.choice(
                    A_MEJORAR) if asistio_empresas else '',
                asistio_feria_laboratorios=asistio_laboratorios,
                evaluacion_feria_laboratorios=random.choice(
                    EVAL_FERIA) if asistio_laboratorios else '',
                conocio_proyectos=random.choice(
                    CONOCIO) if asistio_laboratorios else '',
                lab_interesante='Laboratorio de materiales' if asistio_laboratorios else '',
                mejoras_feria_laboratorios=random.choice(
                    A_MEJORAR) if asistio_laboratorios else '',
                proxima_edicion=random.choice(PROXIMA),
                completada=True,
            )

            # TalkRatings
            regs = Registration.objects.filter(
                dni=cert.dni, attended=True).select_related('talk')
            for reg in regs:
                TalkRating.objects.get_or_create(
                    survey=survey,
                    talk=reg.talk,
                    defaults={
                        'puntuacion_disertante': random.choices([1, 2, 3, 4, 5], weights=[3, 7, 15, 35, 40])[0],
                        'puntuacion_contenido': random.choices([1, 2, 3, 4, 5], weights=[3, 7, 15, 35, 40])[0],
                        'comentario': random.choice(['Muy buena charla', 'Interesante', 'Podría mejorar el tiempo', '']),
                    }
                )

            created += 1
            self.stdout.write(self.style.SUCCESS(
                f'  ✔ {cert.apellido}, {cert.nombre}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nEncuestas creadas: {created}'))
