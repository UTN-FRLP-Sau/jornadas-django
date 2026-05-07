from django.contrib import admin
from .models import Talk, Registration


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'date', 'time', 'capacity', 'registered_count', 'remaining_capacity')
    list_filter = ('department', 'target_year')
    search_fields = ('title', 'speaker', 'description')
    ordering = ('date', 'time')
    readonly_fields = ('registered_count', 'remaining_capacity')
    fieldsets = (
        ('Información Principal', {
            'fields': ('title', 'description', 'speaker', 'image')
        }),
        ('Fecha y Horario', {
            'fields': ('date', 'time')
        }),
        ('Clasificación', {
            'fields': ('department', 'target_year', 'capacity')
        }),
    )


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'dni', 'legajo', 'correo', 'talk', 'attended', 'registered_at')
    list_filter = ('attended', 'talk__department', 'talk')
    search_fields = ('apellido', 'nombre', 'dni', 'legajo', 'correo')
    list_editable = ('attended',)
    ordering = ('talk', 'apellido', 'nombre')
    readonly_fields = ('token', 'registered_at')


# Personalización del sitio admin
admin.site.site_header = "Jornadas de Formación Profesional — Administración"
admin.site.site_title = "JFP Admin"
admin.site.index_title = "Panel de Control"
