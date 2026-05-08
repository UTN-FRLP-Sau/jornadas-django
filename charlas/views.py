from django.core.mail import get_connection
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.contrib.auth import views as auth_views

from .forms import RegistrationForm, TalkForm
from .models import Registration, Talk

import openpyxl
from openpyxl.styles import Font


# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────

def login_required_json(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'No autenticado.'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def _build_qr_content(registration):
    return f"{registration.apellido}|{registration.legajo}|{registration.dni}|{registration.talk_id}|{registration.token}"


def _send_confirmation_email(request, registration):
    talk = registration.talk
    cancel_url = f"{settings.SITE_URL}/cancel/{registration.token}/"

    # Generar QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(_build_qr_content(registration))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    qr_bytes = buf.getvalue()

    html_body = f"""
    <h3>¡Hola {registration.nombre}!</h3>
    <p>Tu inscripción a la charla <b>{talk.title}</b> ha sido confirmada.</p>
    <p><b>Fecha:</b> {talk.date} | <b>Hora:</b> {talk.time} | <b>Disertante:</b> {talk.speaker}</p>
    <p>Para asistir el día del evento, presentá el siguiente código QR en la entrada:</p>
    <img src="cid:qr_code" alt="QR Asistencia" />
    <br><br>
    <p>Si no puedes asistir, cancelá tu inscripción para liberar el cupo:</p>
    <p><a href="{cancel_url}">{cancel_url}</a></p>
    """

    try:
        msg = MIMEMultipart('related')
        msg['Subject'] = f'Confirmación de Inscripción: {talk.title}'
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = registration.correo

        alt = MIMEMultipart('alternative')
        msg.attach(alt)
        alt.attach(MIMEText(html_body, 'html'))

        img_mime = MIMEImage(qr_bytes)
        img_mime.add_header('Content-ID', '<qr_code>')
        img_mime.add_header('Content-Disposition', 'inline',
                            filename='qr_asistencia.png')
        msg.attach(img_mime)

        connection = get_connection()
        connection.open()
        connection.connection.sendmail(
            settings.DEFAULT_FROM_EMAIL,
            [registration.correo],
            msg.as_string()
        )
        connection.close()
        return True
    except Exception as exc:
        print(f'[EMAIL] No se pudo enviar a {registration.correo}: {exc}')
        return False


# ────────────────────────────────────────────────────────────────────────────────
# Public views
# ────────────────────────────────────────────────────────────────────────────────

def index(request):
    talks = list(Talk.objects.all())
    
    def get_date_priority(talk):
        d = talk.date.lower()
        if 'martes' in d: return 1
        if 'miércoles' in d or 'miercoles' in d: return 2
        if 'jueves' in d: return 3
        return 4
        
    def normalize_date(talk):
        d = talk.date.lower()
        if 'martes' in d: return 'Martes 19 de Mayo'
        if 'miércoles' in d or 'miercoles' in d: return 'Miércoles 20 de Mayo'
        if 'jueves' in d: return 'Jueves 21 de Mayo'
        return talk.date

    for t in talks:
        t.normalized_date = normalize_date(t)
        
    # Ordenar por prioridad de fecha (Martes, Miercoles, Jueves) y luego por hora
    sorted_talks = sorted(talks, key=lambda t: (get_date_priority(t), t.time))
    
    return render(request, 'charlas/index.html', {'talks': sorted_talks})

def _duplicate_exists(talk, dni, legajo):
    """Check if a registration with the same DNI or legajo already exists for this talk."""
    from django.db.models import Q
    return Registration.objects.filter(talk=talk).filter(
        Q(dni=dni) | Q(legajo=legajo)
    ).exists()


# Rewrite talk_detail to use _duplicate_exists properly
def talk_register(request, pk):
    talk = get_object_or_404(Talk, pk=pk)
    form = RegistrationForm()
    errors = []

    if request.method == 'POST':
        if talk.remaining_capacity <= 0:
            errors = ['Los cupos para esta charla están agotados.']
        else:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                if _duplicate_exists(talk, data['dni'], data['legajo']):
                    errors = [
                        'Ya te encontrás inscripto en esta charla con ese DNI o Legajo.']
                else:
                    token = str(uuid.uuid4())
                    reg = Registration.objects.create(
                        talk=talk,
                        nombre=data['nombre'],
                        apellido=data['apellido'],
                        dni=data['dni'],
                        legajo=data['legajo'],
                        correo=data['correo'],
                        token=token,
                    )
                    email_ok = _send_confirmation_email(request, reg)
                    return render(request, 'charlas/success.html', {
                        'talk': talk,
                        'email_ok': email_ok,
                    })
            else:
                for field_errors in form.errors.values():
                    errors.extend(field_errors)

    return render(request, 'charlas/talk.html', {'talk': talk, 'form': form, 'errors': errors})


def cancel_registration(request, token):
    reg = get_object_or_404(Registration, token=token)
    reg.delete()
    return render(request, 'charlas/cancel_success.html')


# ────────────────────────────────────────────────────────────────────────────────
# Admin views
# ────────────────────────────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    talks = Talk.objects.all()
    return render(request, 'charlas/admin_dashboard.html', {'talks': talks})


""" 
@login_required
def scanner_dashboard(request):
    talks = Talk.objects.all()
    return render(request, 'charlas/scanner_dashboard.html', {'talks': talks})
 """

@login_required
def admin_new_talk(request):
    form = TalkForm()
    if request.method == 'POST':
        form = TalkForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    return render(request, 'charlas/talk_form.html', {
        'form': form,
        'title': 'Crear Nueva Charla',
        'submit_label': 'Crear Charla',
    })


@login_required
def admin_edit_talk(request, pk):
    talk = get_object_or_404(Talk, pk=pk)
    form = TalkForm(instance=talk)
    if request.method == 'POST':
        form = TalkForm(request.POST, request.FILES, instance=talk)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    return render(request, 'charlas/talk_form.html', {
        'form': form,
        'talk': talk,
        'title': 'Editar Charla',
        'submit_label': 'Guardar Cambios',
        'current_image': talk.image if talk.image else None,
    })


@login_required
@require_POST
def admin_delete_talk(request, pk):
    talk = get_object_or_404(Talk, pk=pk)
    talk.delete()
    return redirect('admin_dashboard')


@login_required
def admin_register_student(request, pk):
    talk = get_object_or_404(Talk, pk=pk)
    form = RegistrationForm()
    errors = []

    if request.method == 'POST':
        if talk.remaining_capacity <= 0:
            errors = ['Los cupos para esta charla están agotados.']
        else:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                if _duplicate_exists(talk, data['dni'], data['legajo']):
                    errors = ['Ya se encuentra inscripto en esta charla con ese DNI o Legajo.']
                else:
                    token = str(uuid.uuid4())
                    reg = Registration.objects.create(
                        talk=talk,
                        nombre=data['nombre'],
                        apellido=data['apellido'],
                        dni=data['dni'],
                        legajo=data['legajo'],
                        correo=data['correo'],
                        token=token,
                        attended=True,
                    )
                    _send_confirmation_email(request, reg)
                    return redirect('admin_talk_details', pk=talk.pk)
            else:
                for field_errors in form.errors.values():
                    errors.extend(field_errors)

    return render(request, 'charlas/talk.html', {'talk': talk, 'form': form, 'errors': errors})


@login_required
def admin_talk_details(request, pk):
    talk = get_object_or_404(Talk, pk=pk)
    registrations = talk.registrations.all().order_by('apellido', 'nombre')
    return render(request, 'charlas/admin_talk_details.html', {
        'talk': talk,
        'registrations': registrations,
    })


@login_required
@require_POST
def update_attendance(request, reg_id):
    import json
    reg = get_object_or_404(Registration, pk=reg_id)
    data = json.loads(request.body)
    reg.attended = data.get('attended', False)
    reg.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def admin_delete_registration(request, reg_id):
    reg = get_object_or_404(Registration, pk=reg_id)
    talk_id = reg.talk_id
    reg.delete()
    return redirect('admin_talk_details', pk=talk_id)


@login_required
def admin_scan(request, pk):
    talk = get_object_or_404(Talk, pk=pk)
    return render(request, 'charlas/admin_scan.html', {'talk': talk})


@login_required_json
@require_POST
def api_scan(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

    import json
    data = json.loads(request.body)
    token = data.get('token')
    talk_id = data.get('talk_id')

    if not token or not talk_id:
        return JsonResponse({'success': False, 'message': 'Datos incompletos.'}, status=400)

    try:
        token = data.get('token').split('|')[-1]
        reg = Registration.objects.get(token=token, talk_id=talk_id)
    except Registration.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Código QR inválido para esta charla.'}, status=404)

    if reg.attended:
        return JsonResponse({
            'success': True,
            'message': f'{reg.nombre} {reg.apellido} ya tenía asistencia registrada.',
            'already_attended': True,
        })

    reg.attended = True
    reg.save()
    return JsonResponse({
        'success': True,
        'message': f'Asistencia confirmada para {reg.nombre} {reg.apellido}.',
        'already_attended': False,
    })


@login_required
def export_attendance(request, pk):
    talk = get_object_or_404(Talk, pk=pk)
    registrations = talk.registrations.filter(attended=True).order_by('apellido', 'nombre')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Asistencias'
    headers = ['Apellido', 'Nombre', 'DNI', 'Legajo', 'Correo']
    ws.append(headers)
    for col in range(1, len(headers) + 1):
        ws.cell(row=1, column=col).font = Font(bold=True)

    for reg in registrations:
        ws.append([reg.apellido, reg.nombre, reg.dni, reg.legajo, reg.correo])

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    filename = f"Asistencias_{talk.title.replace(' ', '_')}.xlsx"
    response = HttpResponse(
        out.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
