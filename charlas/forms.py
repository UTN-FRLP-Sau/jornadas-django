from django import forms
from .models import Talk, DEPARTMENT_CHOICES, TARGET_YEAR_CHOICES


class TalkForm(forms.ModelForm):
    class Meta:
        model = Talk
        fields = ['title', 'description', 'speaker', 'date', 'time', 'department', 'capacity', 'target_year', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Inteligencia Artificial en Ingeniería'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'speaker': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Ing. Juan Pérez'}),
            'date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 20 de mayo'}),
            'time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 18:00 a 19:00hs'}),
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
            'time': 'Hora',
            'department': 'Departamento',
            'capacity': 'Cupos Disponibles',
            'target_year': 'Año de Cursada',
            'image': 'Imagen (Logo, foto del orador, etc.) — Opcional',
        }


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
        if data.get('dni') != data.get('dni_repeat'):
            self.add_error('dni_repeat', 'Los DNI no coinciden.')
        if data.get('legajo') != data.get('legajo_repeat'):
            self.add_error('legajo_repeat', 'Los legajos no coinciden.')
        if data.get('correo') != data.get('correo_repeat'):
            self.add_error('correo_repeat', 'Los correos no coinciden.')
        return data


class AdminLoginForm(forms.Form):
    pin = forms.CharField(label='PIN', max_length=20,
                          widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': '••••'}))
