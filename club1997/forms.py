from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Reserva, Cancha, Producto, Venta, DetalleVenta


class ReservaForm(forms.ModelForm):
    """Formulario para crear reservas"""
    
    class Meta:
        model = Reserva
        fields = ['cancha', 'fecha', 'hora_inicio', 'duracion_horas']
        widgets = {
            'cancha': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duracion_horas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        self.fields['fecha'].widget.attrs.update({
            'min': today.strftime('%Y-%m-%d')
        })
    
    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        duracion = cleaned_data.get('duracion_horas')
        
        # Obtener fecha y hora actual en zona horaria de Colombia
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        # Validar fecha futura
        if fecha:
            if fecha < today:
                raise ValidationError("No puedes reservar en fechas pasadas.")
            # Si es hoy, validar que la hora sea futura
            if fecha == today and hora_inicio:
                if hora_inicio <= current_time:
                    raise ValidationError("No puedes reservar en horas que ya pasaron.")
        
        # Validar duración mínima
        if duracion and duracion < 1:
            raise ValidationError("La duración mínima es de 1 hora.")
        
        # Validar horario de operación (8:00 - 23:00)
        if hora_inicio:
            if hora_inicio.hour < 8 or hora_inicio.hour >= 23:
                raise ValidationError("El horario de operación es de 8:00 a 23:00.")
        
        return cleaned_data


class PagoForm(forms.Form):
    """Formulario para registrar pagos"""
    METODO_PAGO_CHOICES = [
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta', 'Tarjeta de Crédito'),
        ('efectivo', 'Efectivo'),
    ]
    
    monto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monto'})
    )
    metodo = forms.ChoiceField(
        choices=METODO_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    referencia = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Referencia (ej: número de transferencia)'
        })
    )


class CanchaForm(forms.ModelForm):
    """Formulario para crear/editar canchas"""
    
    class Meta:
        model = Cancha
        fields = ['nombre', 'tipo', 'capacidad', 'descripcion', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TarifaForm(forms.Form):
    """Formulario para configurar tarifas"""
    FRANJA_CHOICES = [
        ('mañana', 'Mañana (8:00 - 12:00)'),
        ('tarde', 'Tarde (12:00 - 18:00)'),
        ('noche', 'Noche (18:00 - 23:00)'),
    ]
    
    franja = forms.ChoiceField(
        choices=FRANJA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    precio = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Precio por hora'})
    )


class ProductoForm(forms.ModelForm):
    """Formulario para crear/editar productos"""
    
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'precio', 'stock', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class EmpleadoForm(forms.Form):
    """Formulario para crear/editar empleados"""
    ROLE_CHOICES = [
        ('recepcionista', 'Recepcionista'),
        ('administrador', 'Administrador'),
    ]
    
    nombre = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=6
    )
    rol = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class VentaForm(forms.Form):
    """Formulario para crear ventas en PDV"""
    cliente = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        from django.contrib.auth.models import User
        from .models import UserRole
        super().__init__(*args, **kwargs)
        # Cargar solo clientes
        self.fields['cliente'].queryset = User.objects.filter(
            role_profile__role='cliente'
        )
