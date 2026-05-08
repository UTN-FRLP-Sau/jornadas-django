from django import forms
from .models import Talk, DEPARTMENT_CHOICES, TARGET_YEAR_CHOICES


class TalkForm(forms.ModelForm):
    time_start = forms.CharField(label='Hora desde', widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'time'}))
    time_end = forms.CharField(label='Hora hasta', widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'time'}))

    class Meta:
        model = Talk
        fields = ['title', 'description', 'speaker', 'date', 'department', 'capacity', 'target_year', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Inteligencia Artificial en Ingeniería'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'speaker': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Ing. Juan Pérez'}),
            'date': forms.Select(
                choices=[
                    ('', 'Seleccione un día'),
                    ('Martes 19 de Mayo', 'Martes 19 de Mayo'),
                    ('Miércoles 20 de Mayo', 'Miércoles 20 de Mayo'),
                    ('Jueves 21 de Mayo', 'Jueves 21 de Mayo'),
                ],
                attrs={'class': 'form-select'}
            ),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'target_year': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'title': 'Título de la Charla',
            'description': 'Descripción',
            'speaker': 'Disertante',
            'date': 'Fecha',
            'department': 'Departamento',
            'capacity': 'Cupos Disponibles',
            'target_year': 'Año de Cursada',
            'image': 'Imagen (Logo, foto del orador, etc.) — Opcional',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.time:
            parts = self.instance.time.split(' a ')
            if len(parts) == 2:
                self.fields['time_start'].initial = parts[0]
                self.fields['time_end'].initial = parts[1]
            else:
                self.fields['time_start'].initial = self.instance.time

    def save(self, commit=True):
        instance = super().save(commit=False)
        start = self.cleaned_data.get('time_start')
        end = self.cleaned_data.get('time_end')
        if end:
            instance.time = f"{start} a {end}"
        else:
            instance.time = start
        if commit:
            instance.save()
        return instance

class RegistrationForm(forms.Form):
    nombre = forms.CharField(label='Nombre', max_length=100,
                             widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido = forms.CharField(label='Apellido', max_length=100,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    dni = forms.CharField(label='DNI', max_length=20,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    dni_repeat = forms.CharField(label='Repetir DNI', max_length=20,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    legajo = forms.CharField(label='Legajo', max_length=20,
                             widget=forms.TextInput(attrs={'class': 'form-control'}))
    legajo_repeat = forms.CharField(label='Repetir Legajo', max_length=20,
                                    widget=forms.TextInput(attrs={'class': 'form-control'}))
    correo = forms.EmailField(label='Correo Electrónico',
                              widget=forms.EmailInput(attrs={'class': 'form-control'}))
    correo_repeat = forms.EmailField(label='Repetir Correo Electrónico',
                                     widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def clean(self):
        data = super().clean()
        
        dni = data.get('dni')
        if dni and not dni.isdigit():
            self.add_error('dni', 'El DNI debe contener solo números.')
            
        legajo = data.get('legajo')
        if legajo and not legajo.isdigit():
            self.add_error('legajo', 'El legajo debe contener solo números.')

        if data.get('dni') != data.get('dni_repeat'):
            self.add_error('dni_repeat', 'Los DNI no coinciden.')
        if data.get('legajo') != data.get('legajo_repeat'):
            self.add_error('legajo_repeat', 'Los legajos no coinciden.')
        if data.get('correo') != data.get('correo_repeat'):
            self.add_error('correo_repeat', 'Los correos no coinciden.')
        return data
