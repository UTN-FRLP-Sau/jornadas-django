from django.core.management.base import BaseCommand
from charlas.models import Talk


SEED_TALKS = [
    {
        "title": "Inteligencia Artificial en el Desarrollo de Software",
        "description": "Exploraremos cómo las herramientas de IA generativa están transformando el ciclo de vida del software: desde la generación de código hasta el testing automatizado.",
        "speaker": "Ing. Martín Rodríguez",
        "date": "Martes 20 de mayo",
        "time": "16:00 a 17:30 hs",
        "department": "Sistemas",
        "capacity": 60,
        "target_year": "Todos los años",
    },
    {
        "title": "Ciudades Inteligentes y Movilidad Sustentable",
        "description": "Análisis de casos reales de ciudades que integran tecnología IoT, big data y energías renovables para mejorar la calidad de vida urbana.",
        "speaker": "Dra. Laura González",
        "date": "Miércoles 21 de mayo",
        "time": "14:00 a 15:30 hs",
        "department": "Magistral",
        "capacity": 200,
        "target_year": "Todos los años",
    },
    {
        "title": "Hormigón de Alta Resistencia: Nuevas Aplicaciones",
        "description": "Introducción a las mezclas de última generación, aditivos y su uso en estructuras de gran envergadura. Casos de estudio en Argentina.",
        "speaker": "Ing. Carlos Méndez",
        "date": "Martes 20 de mayo",
        "time": "10:00 a 12:00 hs",
        "department": "Civil",
        "capacity": 40,
        "target_year": "4to y 5to",
    },
    {
        "title": "Introducción a la Termodinámica Aplicada",
        "description": "Conceptos fundamentales de termodinámica y su aplicación práctica en procesos industriales y sistemas de energía.",
        "speaker": "Lic. Ana Torres",
        "date": "Jueves 22 de mayo",
        "time": "09:00 a 11:00 hs",
        "department": "Básicas",
        "capacity": 80,
        "target_year": "1er año",
    },
    {
        "title": "Optimización de Procesos Industriales con Lean Manufacturing",
        "description": "Metodologías ágiles para la mejora continua en plantas industriales: 5S, Kaizen y Value Stream Mapping aplicados a la realidad argentina.",
        "speaker": "Ing. Roberto Sánchez",
        "date": "Miércoles 21 de mayo",
        "time": "17:00 a 18:30 hs",
        "department": "Industrial",
        "capacity": 50,
        "target_year": "3er año",
    },
    {
        "title": "Energías Renovables: El Futuro de la Matriz Energética",
        "description": "Estado actual y perspectivas de la energía solar, eólica e hidráulica en Argentina. Proyectos regionales y oportunidades laborales.",
        "speaker": "Dra. Sofía Ramírez",
        "date": "Jueves 22 de mayo",
        "time": "15:00 a 17:00 hs",
        "department": "Eléctrica",
        "capacity": 70,
        "target_year": "Todos los años",
    },
    {
        "title": "Diseño de Sistemas Mecatrónicos",
        "description": "Integración de sistemas mecánicos, electrónicos y de control en aplicaciones industriales modernas: robótica, automatización y manufactura.",
        "speaker": "Ing. Pablo Fernández",
        "date": "Martes 20 de mayo",
        "time": "18:00 a 19:30 hs",
        "department": "Mecánica",
        "capacity": 45,
        "target_year": "4to y 5to",
    },
    {
        "title": "Procesos Biotecnológicos en la Industria Farmacéutica",
        "description": "Cómo la ingeniería química potencia la producción de fármacos, vacunas y biomateriales. Oportunidades de inserción laboral en el sector.",
        "speaker": "Dra. Valeria Moreno",
        "date": "Jueves 22 de mayo",
        "time": "11:00 a 12:30 hs",
        "department": "Química",
        "capacity": 35,
        "target_year": "2do año",
    },
]


class Command(BaseCommand):
    help = "Carga charlas de ejemplo en la base de datos (seed)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Eliminar todas las charlas existentes antes de hacer el seed.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Talk.objects.count()
            Talk.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"  âœ— Eliminadas {count} charlas existentes."))

        created = 0
        skipped = 0
        for data in SEED_TALKS:
            talk, was_created = Talk.objects.get_or_create(
                title=data['title'],
                defaults=data,
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  âœ“ Creada: {talk.title}"))
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"  â†’ Ya existe: {talk.title}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Seed completo: {created} charlas creadas, {skipped} ya existÃ­an."
        ))

