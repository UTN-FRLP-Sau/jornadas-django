from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public
    path('', views.index, name='index'),
    path('talk/<int:pk>/', views.talk_register, name='talk_register'),
    path('cancel/<str:token>/', views.cancel_registration,
         name='cancel_registration'),

    # Auth
    path('admin/login/', auth_views.LoginView.as_view(
        template_name='charlas/admin_login.html'), name='admin_login'),
    path('admin/logout/', auth_views.LogoutView.as_view(next_page='index'),
         name='admin_logout'),

    # Admin dashboard & CRUD
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/talk/new/', views.admin_new_talk, name='admin_new_talk'),
    path('admin/talk/<int:pk>/edit/',
         views.admin_edit_talk, name='admin_edit_talk'),
    path('admin/talk/<int:pk>/delete/',
         views.admin_delete_talk, name='admin_delete_talk'),
    path('admin/talk/<int:pk>/details/',
         views.admin_talk_details, name='admin_talk_details'),
    path('admin/talk/<int:pk>/register/',
         views.admin_register_student, name='admin_register_student'),
    path('admin/talk/<int:pk>/export/',
         views.export_attendance, name='export_attendance'),
    path('admin/talks/export/', views.export_talks, name='export_talks'),
    path('admin/cronograma/pdf/', views.export_cronograma_pdf,
         name='export_cronograma_pdf'),

    # Attendance
    path('admin/attendance/<int:reg_id>/',
         views.update_attendance, name='update_attendance'),
    path('admin/registration/<int:reg_id>/delete/',
         views.admin_delete_registration, name='admin_delete_registration'),
    path('admin/attendance/import/',
         views.import_attendance, name='import_attendance'),
    path('admin/attendance/import/export/',
         views.export_import_results, name='export_import_results'),
    
    # Dashboard
    path('admin/dashboard/asistencia/',
         views.attendance_dashboard, name='attendance_dashboard'),

    # QR Scanner
    path('admin/scan/<int:pk>/', views.admin_scan, name='admin_scan'),
    path('admin/api/scan/', views.api_scan, name='api_scan'),
    
    # Certificados
    path('admin/certificados/', views.certificate_dashboard,
         name='certificate_dashboard'),
    path('admin/certificados/config/',
         views.certificate_config, name='certificate_config'),
    path('admin/certificados/emitir/',
         views.certificate_emit, name='certificate_emit'),
    path('admin/certificados/emitir/',
         views.certificate_emit, name='certificate_emit'),
    path('admin/certificados/emitir/<int:job_id>/',
         views.certificate_emit_status, name='certificate_emit_status'),
    path('admin/certificados/emitir/<int:job_id>/api/',
         views.certificate_emit_status_api, name='certificate_emit_status_api'),
    path('certificado/validar/', views.certificate_validate,
         name='certificate_validate'),
    path('certificado/descarga/', views.certificate_download,
         name='certificate_download'),
    
    # Encuesta
    path('certificado/encuesta/<str:dni>/', views.survey, name='survey'),
    path('certificado/encuesta/<str:dni>/<int:step>/',
         views.survey, name='survey_step'),
    path('certificado/encuesta/<str:dni>/listo/',
         views.survey_done, name='survey_done'),
]
