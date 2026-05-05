"""
URL configuration for club1997 project.
"""
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Autenticación
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards
    path('dashboard/cliente/', views.cliente_dashboard, name='cliente_dashboard'),
    path('dashboard/recepcionista/', views.recepcionista_dashboard, name='recepcionista_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Canchas (Admin)
    path('admin/canchas/', views.admin_canchas_list, name='admin_canchas_list'),
    path('admin/canchas/crear/', views.admin_cancha_crear, name='admin_cancha_crear'),
    path('admin/canchas/<int:cancha_id>/editar/', views.admin_cancha_editar, name='admin_cancha_editar'),
    path('admin/canchas/<int:cancha_id>/tarifas/', views.admin_cancha_tarifas, name='admin_cancha_tarifas'),
    path('admin/canchas/<int:cancha_id>/eliminar/', views.admin_cancha_eliminar, name='admin_cancha_eliminar'),
    
    # Reservas
    path('reservas/crear/', views.reserva_crear, name='reserva_crear'),
    path('reservas/<int:reserva_id>/', views.reserva_detalle, name='reserva_detalle'),
    path('reservas/<int:reserva_id>/pago/', views.registrar_pago, name='registrar_pago'),
    
    # Pagos en Efectivo (Recepcionista)
    path('pagos/<int:pago_id>/aceptar/', views.aceptar_pago_efectivo, name='aceptar_pago_efectivo'),
    path('pagos/<int:pago_id>/rechazar/', views.rechazar_pago_efectivo, name='rechazar_pago_efectivo'),
    
    # APIs para disponibilidad
    path('api/disponibilidad/', views.verificar_disponibilidad_api, name='verificar_disponibilidad_api'),
    path('api/horarios-disponibles/', views.horarios_disponibles_api, name='horarios_disponibles_api'),
    
    # Facturas
    path('facturas/', views.facturas_lista, name='facturas_lista'),
    path('facturas/<int:factura_id>/', views.factura_detalle, name='factura_detalle'),
    
    # Productos (Admin)
    path('admin/productos/', views.admin_productos_list, name='admin_productos_list'),
    path('admin/productos/crear/', views.admin_producto_crear, name='admin_producto_crear'),
    path('admin/productos/<int:producto_id>/editar/', views.admin_producto_editar, name='admin_producto_editar'),
    path('admin/productos/<int:producto_id>/eliminar/', views.admin_producto_eliminar, name='admin_producto_eliminar'),
    
    # Punto de Venta (Recepcionista)
    path('pdv/venta/', views.pdv_nueva_venta, name='pdv_nueva_venta'),
    
    # Empleados (Admin)
    path('admin/empleados/', views.admin_empleados_list, name='admin_empleados_list'),
    path('admin/empleados/crear/', views.admin_empleado_crear, name='admin_empleado_crear'),
    path('admin/empleados/<int:empleado_id>/editar/', views.admin_empleado_editar, name='admin_empleado_editar'),
    path('admin/empleados/<int:empleado_id>/desactivar/', views.admin_empleado_desactivar, name='admin_empleado_desactivar'),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
