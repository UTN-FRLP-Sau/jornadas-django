from django.db import models

DEPARTMENT_CHOICES = [
    ('Magistral', 'Magistral'),
    ('Básicas', 'Básicas'),
    ('Civil', 'Civil'),
    ('Industrial', 'Industrial'),
    ('Sistemas', 'Sistemas'),
    ('Química', 'Química'),
    ('Eléctrica', 'Eléctrica'),
    ('Mecánica', 'Mecánica'),
]

TARGET_YEAR_CHOICES = [
    ('Todos los años', 'Todos los años'),
    ('1er año', '1er año'),
    ('2do año', '2do año'),
    ('3er año', '3er año'),
    ('4to año', '4to año'),
    ('5to año', '5to año'),
    ('1ero y 2do', '1ero y 2do año'),
    ('4to y 5to', '4to y 5to año'),
]


class Talk(models.Model):
    title = models.CharField('Título', max_length=255)
    description = models.TextField('Descripción')
    speaker = models.CharField('Disertante', max_length=255)
    date = models.CharField('Fecha', max_length=100)
    time = models.CharField('Hora', max_length=100)
    department = models.CharField('Departamento', max_length=50, choices=DEPARTMENT_CHOICES)
    capacity = models.PositiveIntegerField('Cupos')
    target_year = models.CharField('Año de Cursada', max_length=50, choices=TARGET_YEAR_CHOICES, default='Todos los años')
    image = models.ImageField('Imagen', upload_to='talk_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Charla'
        verbose_name_plural = 'Charlas'
        ordering = ['date', 'time']

    def __str__(self):
        return self.title

    @property
    def registered_count(self):
        return self.registrations.count()

    @property
    def remaining_capacity(self):
        return self.capacity - self.registered_count


class Registration(models.Model):
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE, related_name='registrations')
    nombre = models.CharField('Nombre', max_length=100)
    apellido = models.CharField('Apellido', max_length=100)
    dni = models.CharField('DNI', max_length=20)
    legajo = models.CharField('Legajo', max_length=20)
    correo = models.EmailField('Correo Electrónico')
    attended = models.BooleanField('Asistió', default=False)
    token = models.CharField('Token', max_length=36, unique=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'

    def __str__(self):
        return f"{self.apellido}, {self.nombre} → {self.talk.title}"
