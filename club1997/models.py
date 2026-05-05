from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta


class UserRole(models.Model):
    """Extensión del modelo User para definir roles"""
    ROLE_CHOICES = [
        ('cliente', 'Cliente'),
        ('recepcionista', 'Recepcionista'),
        ('administrador', 'Administrador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cliente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"


class Cancha(models.Model):
    """Modelo para las canchas disponibles"""
    TIPO_CHOICES = [
        ('futbol5', 'Fútbol 5'),
        ('futbol7', 'Fútbol 7'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    capacidad = models.IntegerField(validators=[MinValueValidator(1)])
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True, help_text="Indica si la cancha está activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_display()}"
    
    class Meta:
        verbose_name = "Cancha"
        verbose_name_plural = "Canchas"


class TarifaHoraria(models.Model):
    """Modelo para las tarifas por franja horaria"""
    FRANJA_CHOICES = [
        ('mañana', 'Mañana (8:00 - 12:00)'),
        ('tarde', 'Tarde (12:00 - 18:00)'),
        ('noche', 'Noche (18:00 - 23:00)'),
    ]
    
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, related_name='tarifas')
    franja = models.CharField(max_length=20, choices=FRANJA_CHOICES)
    precio_por_hora = models.IntegerField(validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tarifa Horaria"
        verbose_name_plural = "Tarifas Horarias"
        unique_together = ('cancha', 'franja')
    
    def __str__(self):
        return f"{self.cancha.nombre} - {self.get_franja_display()}: ${self.precio_por_hora}/hora"


class Reserva(models.Model):
    """Modelo para las reservas de canchas"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Pago'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta', 'Tarjeta de Crédito'),
        ('efectivo', 'Efectivo'),
    ]
    
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    duracion_horas = models.IntegerField(validators=[MinValueValidator(1)], help_text="Duración en horas")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, null=True, blank=True)
    valor_total = models.IntegerField(validators=[MinValueValidator(0)])
    valor_pagado = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Para pagos en efectivo con límite de tiempo
    fecha_vencimiento_efectivo = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Reserva {self.id} - {self.cancha.nombre} ({self.fecha})"
    
    def get_hora_fin(self):
        """Calcula la hora de fin de la reserva"""
        from datetime import datetime, timedelta
        inicio = datetime.combine(self.fecha, self.hora_inicio)
        fin = inicio + timedelta(hours=self.duracion_horas)
        return fin.time()
    
    def get_falta_pagar(self):
        """Calcula el monto faltante por pagar"""
        return self.valor_total - self.valor_pagado
    
    def es_pago_incompleto(self):
        """Verifica si falta pagar más del 50%"""
        minimo_50_porciento = int(self.valor_total * 0.5)
        return self.valor_pagado < minimo_50_porciento
    
    def verifica_vencimiento_efectivo(self):
        """Verifica si el pago en efectivo venció y cancela si es necesario"""
        if self.metodo_pago == 'efectivo' and self.estado == 'pendiente':
            if self.fecha_vencimiento_efectivo and timezone.now() > self.fecha_vencimiento_efectivo:
                self.estado = 'cancelada'
                self.save()
                return True
        return False
    
    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-created_at']


class Producto(models.Model):
    """Modelo para productos de venta (alimentos y bebidas)"""
    CATEGORIA_CHOICES = [
        ('alimento', 'Alimento'),
        ('bebida', 'Bebida'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    precio = models.IntegerField(validators=[MinValueValidator(0)])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True, help_text="Imagen del producto")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre} (${self.precio})"
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"


class Venta(models.Model):
    """Modelo para ventas de productos"""
    recepcionista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ventas')
    cliente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras')
    valor_total = models.IntegerField(validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Venta {self.id} - ${self.valor_total}"
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-created_at']


class DetalleVenta(models.Model):
    """Detalles de los productos en una venta"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.IntegerField()
    subtotal = models.IntegerField()
    
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"
    
    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"


class Factura(models.Model):
    """Modelo para facturas"""
    TIPO_CHOICES = [
        ('reserva', 'Reserva'),
        ('venta', 'Venta'),
    ]
    
    numero_factura = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='facturas', null=True, blank=True)
    reserva = models.OneToOneField(Reserva, on_delete=models.SET_NULL, null=True, blank=True, related_name='factura')
    venta = models.OneToOneField(Venta, on_delete=models.SET_NULL, null=True, blank=True, related_name='factura')
    valor_total = models.IntegerField()
    fecha_emision = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Factura {self.numero_factura}"
    
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha_emision']


class Pago(models.Model):
    """Modelo para registrar pagos realizados"""
    METODO_CHOICES = [
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta', 'Tarjeta de Crédito'),
        ('efectivo', 'Efectivo'),
    ]
    
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='pagos')
    monto = models.IntegerField(validators=[MinValueValidator(0)])
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    referencia = models.CharField(max_length=100, blank=True, null=True, help_text="Referencia del pago (número de transferencia, etc)")
    estado = models.CharField(max_length=20, default='pendiente', choices=[
        ('pendiente_aceptacion', 'Pendiente de Aceptacion'),
        ('confirmado', 'Confirmado'),
        ('rechazado', 'Rechazado'),
    ])
    # Timer para pagos en efectivo (20 minutos para aceptar)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Pago {self.id} - Reserva {self.reserva.id} - ${self.monto}"
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-created_at']
