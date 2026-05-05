from django.contrib import admin
from .models import UserRole, Cancha, TarifaHoraria, Reserva, Producto, Venta, DetalleVenta, Factura, Pago


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'capacidad', 'estado', 'created_at')
    list_filter = ('tipo', 'estado', 'created_at')
    search_fields = ('nombre',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TarifaHoraria)
class TarifaHorariaAdmin(admin.ModelAdmin):
    list_display = ('cancha', 'franja', 'precio_por_hora', 'updated_at')
    list_filter = ('franja', 'cancha__tipo')
    search_fields = ('cancha__nombre',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'cancha', 'fecha', 'hora_inicio', 'estado', 'valor_total', 'valor_pagado')
    list_filter = ('estado', 'fecha', 'cancha__tipo', 'metodo_pago')
    search_fields = ('cliente__email', 'cancha__nombre')
    readonly_fields = ('created_at', 'updated_at', 'get_hora_fin')
    
    fieldsets = (
        ('Información de Reserva', {
            'fields': ('cliente', 'cancha', 'fecha', 'hora_inicio', 'duracion_horas', 'get_hora_fin')
        }),
        ('Pago', {
            'fields': ('estado', 'metodo_pago', 'valor_total', 'valor_pagado')
        }),
        ('Pago en Efectivo', {
            'fields': ('fecha_vencimiento_efectivo',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'updated_at')
    list_filter = ('categoria', 'created_at')
    search_fields = ('nombre',)
    readonly_fields = ('created_at', 'updated_at')


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'recepcionista', 'cliente', 'valor_total', 'created_at')
    list_filter = ('created_at', 'recepcionista')
    search_fields = ('cliente__email', 'recepcionista__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DetalleVentaInline]


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('venta__created_at',)
    search_fields = ('producto__nombre', 'venta__id')
    readonly_fields = ('subtotal',)


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero_factura', 'tipo', 'cliente', 'valor_total', 'fecha_emision')
    list_filter = ('tipo', 'fecha_emision')
    search_fields = ('numero_factura', 'cliente__email')
    readonly_fields = ('numero_factura', 'fecha_emision')


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'reserva', 'monto', 'metodo', 'estado', 'created_at')
    list_filter = ('estado', 'metodo', 'created_at')
    search_fields = ('reserva__id', 'referencia')
    readonly_fields = ('created_at', 'updated_at')
