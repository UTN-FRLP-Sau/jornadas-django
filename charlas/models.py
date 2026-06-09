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
    attended_reclamo = models.BooleanField(
        'Presente por reclamo', default=False)

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
    encuesta_obligatoria = models.BooleanField(
        'Encuesta obligatoria para descargar', default=True)
    mensaje_bloqueado = models.TextField('Mensaje cuando está bloqueado', default='La descarga de certificados aún no está habilitada. Te avisaremos por correo cuando esté disponible.')
    dias_reclamo = models.PositiveIntegerField(
        'Días para reclamar', default=7,
        help_text='Se usa solo si no se establece una fecha fija de cierre.')
    dias_respuesta = models.PositiveIntegerField('Días para responder', default=20)
    fecha_cierre_reclamo = models.DateField(
        'Fecha de cierre de reclamos', null=True, blank=True,
        help_text='Fecha fija hasta la que se aceptan reclamos. '
                  'Si se deja en blanco, se calcula automáticamente sumando '
                  '"Días para reclamar" a la fecha de envío de certificados.')

    class Meta:
        verbose_name = 'Configuración de Certificados'
        verbose_name_plural = 'Configuraciones de Certificados'

    def __str__(self):
        return f"{self.get_modalidad_display()} — mín. {self.minimo} {'+ magistral' if self.requiere_magistral else ''}"

    def get_fecha_cierre_reclamo(self):
        """Devuelve la fecha de cierre de reclamos: fija si está seteada, calculada si no."""
        if self.fecha_cierre_reclamo:
            return self.fecha_cierre_reclamo
        from datetime import timedelta
        from charlas.models import EmissionJob
        ultimo_job = EmissionJob.objects.filter(status='completado').order_by('-finished_at').first()
        if ultimo_job and ultimo_job.finished_at:
            return ultimo_job.finished_at.date() + timedelta(days=1) + timedelta(days=self.dias_reclamo)
        return None


class Certificate(models.Model):
    
    TIPO_CERT_CHOICES = [
        ('diploma', 'Diploma de asistencia'),
        ('constancia_parcial', 'Constancia de participación parcial'),
        ('constancia_justificacion', 'Constancia de justificación'),
    ]

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
    tipo = models.CharField('Tipo', max_length=30,
                            choices=TIPO_CERT_CHOICES, default='diploma')

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


class Reclamo(models.Model):
    TIPO_CHOICES = [
        ('asistencia', 'Fui pero no se registró mi presente'),
        ('justificacion', 'Ausencia justificada'),
    ]
    MOTIVO_CHOICES = [
        ('no_registrado', 'Fui a una charla pero no se me registró el presente'),
        ('trabajo', 'No pude asistir a las jornadas por trabajo'),
        ('no_cursa', 'No asistí a charlas de un día porque no curso ese día'),
        ('superposicion', 'El cambio de horario generó una superposición de charlas'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('ampliacion', 'Ampliación solicitada'),
    ]
    RESOLUCION_CHOICES = [
        ('charla', 'Perdonar charla/s específica/s'),
        ('dia', 'Perdonar día/s completo/s'),
        ('certificado_directo', 'Emitir certificado directamente'),
        ('asistencia', 'Marcar asistencia como presente'),
    ]
    CARRERA_CHOICES = [
        ('Industrial', 'Ingeniería Industrial'),
        ('Sistemas', 'Ingeniería en Sistemas de Información'),
        ('Mecánica', 'Ingeniería Mecánica'),
        ('Química', 'Ingeniería Química'),
        ('Civil', 'Ingeniería Civil'),
        ('Eléctrica', 'Ingeniería en Energía Eléctrica'),
    ]

    # Datos del alumno
    dni = models.CharField('DNI', max_length=20)
    legajo = models.CharField('Legajo', max_length=20)
    nombre = models.CharField('Nombre', max_length=100)
    apellido = models.CharField('Apellido', max_length=100)
    carrera = models.CharField(
        'Carrera', max_length=50, choices=CARRERA_CHOICES)
    correo = models.EmailField('Correo')
    

    # Reclamo
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    motivo = models.CharField('Motivo', max_length=30, choices=MOTIVO_CHOICES)
    descripcion = models.TextField('Descripción')
    talk = models.ForeignKey(Talk, on_delete=models.SET_NULL, null=True,
                             blank=True, related_name='reclamos', verbose_name='Charla')
    dia = models.CharField('Día', max_length=50, blank=True, default='')
    archivo = models.FileField(
        'Adjunto', upload_to='reclamos/', blank=True, null=True)
    dias_perdonados_list = models.JSONField(
        'Días perdonados', default=list, blank=True)
    charlas_perdonadas_count = models.PositiveSmallIntegerField(
        'Charlas perdonadas', default=0)

    # Estado
    estado = models.CharField('Estado', max_length=20,
                              choices=ESTADO_CHOICES, default='pendiente')
    resolucion = models.CharField(
        'Resolución', max_length=30, choices=RESOLUCION_CHOICES, blank=True, default='')
    nota_admin = models.TextField(
        'Nota del administrador', blank=True, default='')
    nota_ampliacion = models.TextField(
        'Solicitud de ampliación', blank=True, default='')
    respuesta_ampliacion = models.TextField(
        'Respuesta de ampliación', blank=True, default='')

    # Charlas/días perdonados
    charlas_perdonadas = models.ManyToManyField(
        Talk, blank=True, related_name='perdonadas')
    dias_perdonados = models.CharField(
        'Días perdonados', max_length=200, blank=True, default='')

    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    fecha_cierre_reclamo = models.DateField(
        'Cierre de reclamos', null=True, blank=True)
    fecha_cierre_respuesta = models.DateField(
        'Cierre de respuestas', null=True, blank=True)

    class Meta:
        verbose_name = 'Reclamo'
        verbose_name_plural = 'Reclamos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"#{self.pk} — {self.apellido}, {self.nombre} ({self.get_estado_display()})"

    @property
    def vencido(self):
        from django.utils import timezone
        if self.estado == 'pendiente' and self.fecha_cierre_respuesta:
            return timezone.now().date() > self.fecha_cierre_respuesta
        return False
