import threading

from django.db.models.signals import post_save
from django.dispatch import receiver


def _limpiar_certificados_no_elegibles(config_id):
    """
    Elimina certificados de alumnos que ya no califican con la nueva config.
    NO emite certificados nuevos — eso sigue siendo un proceso manual.
    """
    from charlas.models import Certificate, CertificateConfig, Registration, Reclamo, Talk
    from charlas.views import _evaluar_alumno

    config = CertificateConfig.objects.get(id=config_id)
    dias_jornada = set(Talk.objects.values_list('date', flat=True).distinct())

    dnis_con_asistencia = set(
        Registration.objects.filter(attended=True).values_list('dni', flat=True)
    )
    dnis_con_reclamo = set(
        Reclamo.objects.filter(estado='aprobado').values_list('dni', flat=True)
    )
    todos_dnis = dnis_con_asistencia | dnis_con_reclamo

    elegibles = {dni for dni in todos_dnis if _evaluar_alumno(dni, config, dias_jornada)}

    dnis_con_cert = set(Certificate.objects.values_list('dni', flat=True))
    no_califican = dnis_con_cert - elegibles

    if no_califican:
        Certificate.objects.filter(dni__in=no_califican).delete()
        print(f'[SIGNAL] Eliminados {len(no_califican)} certificados por cambio de config.')
    else:
        print('[SIGNAL] Ningún certificado eliminado — todos los emitidos siguen calificando.')


@receiver(post_save, sender='charlas.CertificateConfig')
def on_config_guardada(sender, instance, **kwargs):
    if not instance.activa:
        return
    t = threading.Thread(target=_limpiar_certificados_no_elegibles, args=(instance.id,), daemon=True)
    t.start()
