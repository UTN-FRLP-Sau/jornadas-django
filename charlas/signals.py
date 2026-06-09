import threading

from django.db.models.signals import post_save
from django.dispatch import receiver


def _recalcular_certificados(config_id):
    from charlas.models import Certificate, CertificateConfig, Registration, Reclamo, Talk
    from charlas.views import _evaluar_alumno, _generate_certificate_pdf, _send_certificate_email

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

    certs_actuales = {c.dni: c for c in Certificate.objects.all()}

    # Eliminar certificados de quienes ya no califican
    no_califican = set(certs_actuales.keys()) - elegibles
    if no_califican:
        Certificate.objects.filter(dni__in=no_califican).delete()
        print(f'[SIGNAL] Eliminados {len(no_califican)} certificados por cambio de config.')

    # Emitir certificados para nuevos elegibles
    nuevos = elegibles - set(certs_actuales.keys())
    for dni in nuevos:
        reg = Registration.objects.filter(dni=dni, attended=True).select_related('talk').first()
        if reg:
            nombre, apellido, legajo, correo = reg.nombre, reg.apellido, reg.legajo, reg.correo
        else:
            reclamo = Reclamo.objects.filter(dni=dni, estado='aprobado').first()
            if not reclamo:
                continue
            nombre, apellido, legajo, correo = reclamo.nombre, reclamo.apellido, reclamo.legajo, reclamo.correo

        cert = Certificate.objects.create(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            legajo=legajo,
            correo=correo,
            config=config,
        )
        try:
            archivo = _generate_certificate_pdf(cert)
            cert.archivo = archivo
            cert.save()
            _send_certificate_email(cert)
        except Exception as e:
            print(f'[SIGNAL] Error generando certificado para {dni}: {e}')

    print(f'[SIGNAL] Recalculo completado: {len(elegibles)} elegibles, {len(nuevos)} nuevos, {len(no_califican)} eliminados.')


@receiver(post_save, sender='charlas.CertificateConfig')
def on_config_guardada(sender, instance, **kwargs):
    if not instance.activa:
        return
    t = threading.Thread(target=_recalcular_certificados, args=(instance.id,), daemon=True)
    t.start()
