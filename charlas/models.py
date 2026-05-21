import string
import secrets
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
    location = models.CharField(
        'Ubicación', max_length=255, blank=True, default='')

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


def generate_cert_code():
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


class CertificateConfig(models.Model):
    MODALIDAD_CHOICES = [
        ('total', 'Total de charlas'),
        ('por_dia', 'Por día'),
    ]
    modalidad = models.CharField(
        'Modalidad', max_length=10, choices=MODALIDAD_CHOICES, default='total')
    minimo = models.PositiveIntegerField('Mínimo de charlas', default=1)
    requiere_magistral = models.BooleanField(
        'Requiere magistral', default=False)
    activa = models.BooleanField('Configuración activa', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    descarga_habilitada = models.BooleanField('Descarga habilitada', default=False)
    mensaje_bloqueado = models.TextField('Mensaje cuando está bloqueado', default='La descarga de certificados aún no está habilitada. Te avisaremos por correo cuando esté disponible.')

    class Meta:
        verbose_name = 'Configuración de Certificados'
        verbose_name_plural = 'Configuraciones de Certificados'

    def __str__(self):
        return f"{self.get_modalidad_display()} — mín. {self.minimo} {'+ magistral' if self.requiere_magistral else ''}"


class Certificate(models.Model):
    nombre = models.CharField('Nombre', max_length=100)
    apellido = models.CharField('Apellido', max_length=100)
    dni = models.CharField('DNI', max_length=20)
    legajo = models.CharField('Legajo', max_length=20)
    correo = models.EmailField('Correo')
    codigo = models.CharField('Código', max_length=8,
                              unique=True, default=generate_cert_code)
    archivo = models.FileField(
        'Archivo', upload_to='certificados/', blank=True, null=True)
    emitido_at = models.DateTimeField('Emitido el', auto_now_add=True)
    config = models.ForeignKey(
        CertificateConfig, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'

    def __str__(self):
        return f"{self.apellido}, {self.nombre} — {self.codigo}"


class EmissionJob(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pendiente')
    total = models.PositiveIntegerField(default=0)
    enviados = models.PositiveIntegerField(default=0)
    errores = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Job de Emisión'
        verbose_name_plural = 'Jobs de Emisión'

    def __str__(self):
        return f"Job {self.id} — {self.status} ({self.enviados}/{self.total})"


class Survey(models.Model):
    certificate = models.OneToOneField(
        Certificate, on_delete=models.CASCADE, related_name='survey')

    # Datos generales
    carrera = models.CharField(max_length=100, blank=True, default='')
    anio_cursada = models.CharField(max_length=20, blank=True, default='')

    # Evaluación general
    evaluacion_general = models.CharField(
        max_length=20, blank=True, default='')
    aporte_formacion = models.CharField(max_length=20, blank=True, default='')
    interes_tematicas = models.CharField(max_length=20, blank=True, default='')
    organizacion_general = models.PositiveSmallIntegerField(
        null=True, blank=True)

    # Matriz de aspectos
    matriz_variedad = models.CharField(max_length=20, blank=True, default='')
    matriz_disertantes = models.CharField(
        max_length=20, blank=True, default='')
    matriz_horarios = models.CharField(max_length=20, blank=True, default='')
    matriz_informacion = models.CharField(
        max_length=20, blank=True, default='')
    matriz_inscripcion = models.CharField(
        max_length=20, blank=True, default='')
    matriz_acreditacion = models.CharField(
        max_length=20, blank=True, default='')
    matriz_espacios = models.CharField(max_length=20, blank=True, default='')
    matriz_colaboradores = models.CharField(
        max_length=20, blank=True, default='')

    # Preguntas abiertas generales
    lo_mejor = models.TextField(blank=True, default='')
    a_mejorar = models.TextField(blank=True, default='')

    # Feria de empresas
    asistio_feria_empresas = models.BooleanField(null=True, blank=True)
    evaluacion_feria_empresas = models.CharField(
        max_length=20, blank=True, default='')
    utilidad_feria_empresas = models.CharField(
        max_length=20, blank=True, default='')
    stands_interesantes = models.TextField(blank=True, default='')
    mejoras_feria_empresas = models.TextField(blank=True, default='')

    # Feria de laboratorios
    asistio_feria_laboratorios = models.BooleanField(null=True, blank=True)
    evaluacion_feria_laboratorios = models.CharField(
        max_length=20, blank=True, default='')
    conocio_proyectos = models.CharField(max_length=20, blank=True, default='')
    lab_interesante = models.TextField(blank=True, default='')
    mejoras_feria_laboratorios = models.TextField(blank=True, default='')

    # Sección final
    proxima_edicion = models.TextField(blank=True, default='')

    # Control
    completada = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Encuesta'
        verbose_name_plural = 'Encuestas'


class TalkRating(models.Model):
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name='talk_ratings')
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE)
    puntuacion_disertante = models.PositiveSmallIntegerField(
        null=True, blank=True)
    puntuacion_contenido = models.PositiveSmallIntegerField(
        null=True, blank=True)
    comentario = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Puntuación de Charla'
        verbose_name_plural = 'Puntuaciones de Charlas'
        unique_together = ('survey', 'talk')
