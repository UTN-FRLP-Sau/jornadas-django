# Refactor: bugs y code smells — jornadas-django

## Context

Revisión integral del codebase para detectar bugs reales, inconsistencias de modelo y code smells antes de que llegue a producción. El proyecto es un sistema de jornadas universitarias con inscripciones, asistencia, reclamos y emisión de certificados.

---

## Tier 1 — Bugs con comportamiento incorrecto

### 1. Función `certificate_emit` duplicada (dead code)

**Archivo:** `charlas/views.py:1033–1078`  
La primera definición (síncrona) es completamente sobreescrita por la segunda (línea 1082). Python simplemente usa la última. La primera función nunca se ejecuta pero confunde enormemente al lector.  
**Fix:** Eliminar las líneas 1033–1078 completas (el bloque sync sin el EmissionJob).

### 2. `attended_reclamo` no se setea cuando `tipo='asistencia'`

**Archivo:** `charlas/views.py:1835–1842`  
Cuando se aprueba un reclamo con `tipo='asistencia'`, se pone `reg.attended = True` pero NO `reg.attended_reclamo = True`. El código de `resolucion in ('charla', 'dia')` sí lo setea (línea 1872). Los templates usan `attended_reclamo` para mostrar el badge "Presente por reclamo" → inconsistencia silenciosa.  
**Fix:** En el bloque `if reclamo.tipo == 'asistencia'`, agregar `reg.attended_reclamo = True` junto con `reg.attended = True`.

### 3. `reclamo_resolver` no es idempotente

**Archivo:** `charlas/views.py:1931–1946`  
Si un admin hace clic en "aprobar" dos veces (o por doble submit), `_aplicar_resolucion` corre dos veces: puede crear dos certificados, marcar dos veces la asistencia, etc.  
**Fix:** Al inicio del bloque `if accion == 'aprobar':`, agregar un guard:

```python
if reclamo.estado == 'aprobado':
    return redirect('reclamo_detalle', pk=pk)
```

### 4. `_evaluar_alumno` en modo `por_dia` ignora días perdonados si ya existe asistencia real

**Archivo:** `charlas/views.py:387–396`  

```python
for dia in dias_perdonados:
    if dia not in dias:           # ← solo agrega si NO existe
        dias[dia] = config.minimo
```

Si el alumno tiene 1 asistencia en un día y ese día también está perdonado, el perdón no suma al count. En modo `total` sí suma. Incosistencia entre modalidades.  
**Fix:** En modo `por_dia`, para los días perdonados que ya existen, también incrementar el count:

```python
for dia in dias_perdonados:
    dias[dia] = dias.get(dia, 0) + config.minimo
```

---

## Tier 2 — Modelo: campos muertos y faltantes

### 5. `Reclamo.dias_perdonados` (CharField) es campo muerto

**Archivo:** `charlas/models.py:317–318`  
El JSONField `dias_perdonados_list` (línea 297) es el que se lee/escribe en todo el codebase. El CharField `dias_perdonados` no se usa en ninguna view ni template.  
**Fix:** Crear migración para eliminar el campo `dias_perdonados`.

### 6. `Reclamo.charlas_perdonadas` (M2M) es campo muerto

**Archivo:** `charlas/models.py:315–316`  
El M2M `charlas_perdonadas` nunca se popula. `_evaluar_alumno` usa `charlas_perdonadas_count` (PositiveSmallIntegerField). El M2M es confusión pura.  
**Fix:** Crear migración para eliminar el M2M `charlas_perdonadas`. Mantener solo `charlas_perdonadas_count`.

### 7. Falta `db_index` en campos muy filtrados

**Archivo:** `charlas/models.py`  
`Registration.dni`, `Reclamo.dni`, `Certificate.dni` y `Registration.legajo` se usan en `.filter(dni=...)` en decenas de lugares. Sin índice, cada query hace table scan.  
**Fix:** Agregar `db_index=True` a esos cuatro campos y crear la migración.

### 8. Sin `unique_together` en `Registration(talk, dni)`

**Archivo:** `charlas/models.py`  
Un alumno puede inscribirse dos veces a la misma charla si hace doble submit o si el import lo agrega de nuevo. Hay lógica en `_procesar_fila` que lo intenta prevenir en el import, pero no en la inscripción web.  
**Fix:** Agregar `unique_together = ('talk', 'dni')` en `Registration.Meta` + migración.

---

## Tier 3 — Code smells y mantenibilidad

### 9. `print()` en vez de `logging`

**Archivos:** `views.py` líneas 66, 88, 305, 355, 1066, 1864, 1893, 1926, etc.  
Todos los `print(f'[CERT]...')` son invisibles en producción (stdout no va a ningún log en WSGI).  
**Fix:** Al inicio del archivo agregar:

```python
import logging
logger = logging.getLogger(__name__)
```

Y reemplazar todos los `print(f'[X] ...')` por `logger.error(...)` / `logger.warning(...)`.

### 10. `_send_certificate_email` puede dejar conexión abierta

**Archivo:** `charlas/views.py:344–352`  

```python
connection.open()
connection.connection.sendmail(...)  # si explota aquí
connection.close()                   # ← nunca se ejecuta
```

**Fix:** Usar `try/finally` o `with get_connection() as connection:`.

### 11. Fechas hardcodeadas en `reclamo_nuevo`

**Archivo:** `charlas/views.py:1725`  

```python
dias = ['Martes 19 de Mayo', 'Miércoles 20 de Mayo', 'Jueves 21 de Mayo']
```

También en `charlas/forms.py` para el select de días. Si se agrega una charla con otra fecha, el formulario de reclamo no la muestra.  
**Fix:** Derivar los días dinámicamente desde la base de datos:

```python
dias = list(Talk.objects.values_list('date', flat=True).distinct().order_by('date'))
```

Esto funciona bien porque `Talk.date` es un CharField que ya contiene el texto legible ("Martes 19 de Mayo").

### 12. Server-side: validar que `motivo` → `tipo` sean coherentes

**Archivo:** `charlas/views.py:1727–1770`  
El tipo ('asistencia' / 'justificacion') lo determina JavaScript en el cliente. No hay validación server-side. Un usuario malicioso puede enviar `tipo='asistencia'` con `motivo='trabajo'` y se guarda sin error.  
**Fix:** Agregar la misma lógica de mapeo en la view antes del `Reclamo.objects.create`:

```python
MOTIVO_TIPO_MAP = {
    'no_registrado': 'asistencia',
    'superposicion': 'justificacion',
    'trabajo': 'justificacion',
    'no_cursa': 'justificacion',
}
tipo = MOTIVO_TIPO_MAP.get(motivo, tipo)  # override client value
```

### 13. N+1 saves de `EmissionJob` en `_run_emission`

**Archivo:** `charlas/views.py:295`  
`job.save()` se llama una vez por certificado emitido. Con 500 alumnos = 500 writes innecesarios.  
**Fix:** Usar `update_fields` y acumular los contadores:

```python
EmissionJob.objects.filter(pk=job.id).update(
    enviados=F('enviados') + (1 if ok else 0),
    errores=F('errores') + (0 if ok else 1),
)
```

Y solo un `job.save()` al final para cambiar el status.

---

## Archivos a modificar

| Archivo | Cambios |
|---|---|
| `charlas/views.py` | Eliminar primera `certificate_emit` (1033–1078), fijar `attended_reclamo`, guard idempotency, fix `_evaluar_alumno` por_dia, replace print→logging, fix connection leak, dias dinámicos, motivo→tipo server-side, N+1 fix |
| `charlas/models.py` | Agregar `db_index=True` a `dni`/`legajo`, agregar `unique_together` en Registration, eliminar campos muertos (`dias_perdonados` CharField, `charlas_perdonadas` M2M) |
| `charlas/forms.py` | Eliminar dias hardcodeados (si aplica) |
| `charlas/migrations/` | Nueva migración: eliminar campos muertos, agregar índices, agregar unique_together |

---

## Verificación

1. `python manage.py migrate` — aplica sin errores
2. `python manage.py check` — sin warnings
3. Flujo completo: inscribir alumno → marcar asistencia → emitir certificado → descargar
4. Flujo reclamo: crear reclamo → aprobar con `tipo=asistencia` → verificar que `attended_reclamo=True` en Registration
5. Flujo reclamo doble submit: aprobar el mismo reclamo dos veces → segunda vez redirige sin crear duplicado
6. `_evaluar_alumno` con modo `por_dia` y día perdonado + asistencia real → pasa correctamente
