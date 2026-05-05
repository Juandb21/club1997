from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    UserRole, Cancha, TarifaHoraria, Reserva, Producto, Venta, DetalleVenta,
    Factura, Pago
)
from .forms import (
    ReservaForm, PagoForm, CanchaForm, TarifaForm, ProductoForm, EmpleadoForm, VentaForm
)
from .services import (
    TarifaService, DisponibilidadService, PagoService, FacturaService, ReservaService
)


# ============ FUNCIONES AUXILIARES ============

def es_cliente(user):
    """Verifica si el usuario tiene rol de cliente"""
    try:
        return user.role_profile.role == 'cliente'
    except:
        return False

def es_recepcionista(user):
    """Verifica si el usuario tiene rol de recepcionista"""
    try:
        return user.role_profile.role == 'recepcionista'
    except:
        return False

def es_admin(user):
    """Verifica si el usuario tiene rol de administrador"""
    try:
        return user.role_profile.role == 'administrador'
    except:
        return False


# ============ RF-01: PÁGINA DE INICIO ============

def home_view(request):
    """Página de inicio con información del club"""
    canchas = Cancha.objects.filter(estado=True)
    tarifas = TarifaHoraria.objects.select_related('cancha').filter(cancha__estado=True)
    
    context = {
        'canchas': canchas,
        'tarifas': tarifas,
        'franjas': {
            'mañana': 'Mañana (8:00 - 12:00)',
            'tarde': 'Tarde (12:00 - 18:00)',
            'noche': 'Noche (18:00 - 23:00)',
        },
        'horarios_operacion': {
            'inicio': '8:00',
            'fin': '23:00',
        },
        'requisitos': {
            'pago_minimo': '50%',
            'tiempo_minimo': '1 hora',
            'efectivo_limite': '20 minutos',
        }
    }
    return render(request, 'home.html', context)


# ============ RF-02: REGISTRO DE USUARIOS ============

def register_view(request):
    """Registro de nuevos usuarios (clientes por defecto)"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validaciones
        if not nombre or not email or not password:
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('register')
        
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('register')
        
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return redirect('register')
        
        # Verificar email único
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return redirect('register')
        
        # Crear usuario
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=nombre
            )
            
            # Crear perfil de rol (cliente por defecto)
            UserRole.objects.create(
                user=user,
                role='cliente'
            )
            
            messages.success(request, 'Registro exitoso. Por favor inicia sesión.')
            return redirect('login')
        
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')
            return redirect('register')
    
    return render(request, 'register.html')


# ============ RF-03: INICIO DE SESIÓN ============

def login_view(request):
    """Inicio de sesión con validación de rol"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        username = email
        found_user = User.objects.filter(email__iexact=email).first()
        if found_user:
            username = found_user.username
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar que el usuario tenga rol asignado
            try:
                role_profile = user.role_profile
                if not role_profile.is_active:
                    messages.error(request, 'Tu usuario está inactivo. Contacta al administrador.')
                    return redirect('login')
            except UserRole.DoesNotExist:
                messages.error(request, 'No tienes un rol asignado. Contacta al administrador.')
                return redirect('login')
            
            login(request, user)
            
            # Redirigir según rol
            if es_admin(user):
                return redirect('admin_dashboard')
            elif es_recepcionista(user):
                return redirect('recepcionista_dashboard')
            else:
                return redirect('cliente_dashboard')
        else:
            messages.error(request, 'Credenciales incorrectas. Intenta nuevamente.')
    
    return render(request, 'login.html')


def logout_view(request):
    """Cierra la sesión del usuario"""
    logout(request)
    return redirect('/')


# ============ RF-04: GESTIÓN DE CANCHAS (Admin) ============

@login_required
@user_passes_test(es_admin)
def admin_canchas_list(request):
    """Lista todas las canchas"""
    canchas = Cancha.objects.all()
    return render(request, 'admin/canchas/list.html', {'canchas': canchas})


@login_required
@user_passes_test(es_admin)
def admin_cancha_crear(request):
    """Crea una nueva cancha"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')
        capacidad = request.POST.get('capacidad')
        descripcion = request.POST.get('descripcion')
        
        try:
            cancha = Cancha.objects.create(
                nombre=nombre,
                tipo=tipo,
                capacidad=int(capacidad),
                descripcion=descripcion
            )
            messages.success(request, 'Cancha creada exitosamente.')
            return redirect('admin_cancha_tarifas', cancha_id=cancha.id)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('admin_canchas_list')
    
    return render(request, 'admin/canchas/crear.html', {
        'tipos_cancha': Cancha._meta.get_field('tipo').choices
    })


@login_required
@user_passes_test(es_admin)
def admin_cancha_editar(request, cancha_id):
    """Edita una cancha existente"""
    cancha = get_object_or_404(Cancha, id=cancha_id)
    
    if request.method == 'POST':
        cancha.nombre = request.POST.get('nombre')
        cancha.tipo = request.POST.get('tipo')
        cancha.capacidad = int(request.POST.get('capacidad'))
        cancha.descripcion = request.POST.get('descripcion')
        cancha.estado = request.POST.get('estado') == 'on'
        cancha.save()
        
        messages.success(request, 'Cancha actualizada exitosamente.')
        return redirect('admin_canchas_list')
    
    return render(request, 'admin/canchas/editar.html', {
        'cancha': cancha,
        'tipos_cancha': Cancha._meta.get_field('tipo').choices
    })


@login_required
@user_passes_test(es_admin)
def admin_cancha_tarifas(request, cancha_id):
    """Gestiona las tarifas de una cancha"""
    cancha = get_object_or_404(Cancha, id=cancha_id)
    tarifas = TarifaHoraria.objects.filter(cancha=cancha)
    
    if request.method == 'POST':
        franja = request.POST.get('franja')
        precio = request.POST.get('precio')
        
        try:
            tarifa, created = TarifaHoraria.objects.update_or_create(
                cancha=cancha,
                franja=franja,
                defaults={'precio_por_hora': int(precio)}
            )
            messages.success(request, 'Tarifa actualizada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('admin_cancha_tarifas', cancha_id=cancha_id)
    
    # Crear lista de franjas con sus tarifas
    franjas_list = []
    franja_choices = TarifaHoraria._meta.get_field('franja').choices
    tarifas_dict = {t.franja: t for t in tarifas}
    
    for franja_id, franja_nombre in franja_choices:
        franjas_list.append({
            'id': franja_id,
            'nombre': franja_nombre,
            'tarifa': tarifas_dict.get(franja_id)
        })
    
    context = {
        'cancha': cancha,
        'tarifas': tarifas,
        'franjas_list': franjas_list,
    }
    return render(request, 'admin/canchas/tarifas.html', context)


@login_required
@user_passes_test(es_admin)
def admin_cancha_eliminar(request, cancha_id):
    """Elimina una cancha (desactiva)"""
    cancha = get_object_or_404(Cancha, id=cancha_id)
    
    if request.method == 'POST':
        cancha.estado = False
        cancha.save()
        messages.success(request, 'Cancha eliminada (desactivada).')
        return redirect('admin_canchas_list')
    
    return render(request, 'admin/canchas/confirmar_eliminar.html', {'cancha': cancha})


# ============ RF-05 & RF-06: CREACIÓN DE RESERVAS Y VALIDACIÓN DE DISPONIBILIDAD ============

@login_required
@user_passes_test(lambda u: es_cliente(u) or es_recepcionista(u))
def reserva_crear(request):
    """Crea una nueva reserva"""
    if request.method == 'POST':
        cancha_id = request.POST.get('cancha_id')
        fecha_str = request.POST.get('fecha')
        hora_inicio_str = request.POST.get('hora_inicio')
        duracion_horas = int(request.POST.get('duracion_horas', 1))
        
        try:
            cancha = Cancha.objects.get(id=cancha_id, estado=True)
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            
            # Validar que la fecha sea futura
            if fecha < datetime.now().date():
                raise ValueError("No puedes reservar en fechas pasadas.")
            
            # Crear reserva usando el servicio
            cliente = request.user if es_cliente(request.user) else None
            if not cliente and es_recepcionista(request.user):
                cliente_id = request.POST.get('cliente_id')
                cliente = User.objects.get(id=cliente_id)
            
            reserva = ReservaService.crear_reserva(
                cliente=cliente,
                cancha=cancha,
                fecha=fecha,
                hora_inicio=hora_inicio,
                duracion_horas=duracion_horas
            )
            
            messages.success(request, f'Reserva creada. Total: ${reserva.valor_total}')
            return redirect('reserva_detalle', reserva_id=reserva.id)
        
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    canchas = Cancha.objects.filter(estado=True)
    context = {'canchas': canchas}
    
    if es_recepcionista(request.user):
        context['clientes'] = User.objects.filter(role_profile__role='cliente', role_profile__is_active=True)
    
    return render(request, 'reservas/crear.html', context)


@require_http_methods(["GET"])
def verificar_disponibilidad_api(request):
    """API para verificar disponibilidad en tiempo real (AJAX)"""
    cancha_id = request.GET.get('cancha_id')
    fecha = request.GET.get('fecha')
    hora_inicio = request.GET.get('hora_inicio')
    duracion = int(request.GET.get('duracion', 1))
    
    try:
        cancha = Cancha.objects.get(id=cancha_id)
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        hora_obj = datetime.strptime(hora_inicio, '%H:%M').time()
        
        disponible = DisponibilidadService.verificar_disponibilidad(
            cancha, fecha_obj, hora_obj, duracion
        )
        
        valor = TarifaService.calcular_valor_reserva(
            cancha, fecha_obj, hora_obj, duracion
        ) if disponible else None
        
        return JsonResponse({
            'disponible': disponible,
            'valor': float(valor) if valor else None,
            'mensaje': 'Disponible' if disponible else 'No disponible en este horario'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def horarios_disponibles_api(request):
    """API para obtener horarios disponibles (AJAX)"""
    cancha_id = request.GET.get('cancha_id')
    fecha = request.GET.get('fecha')
    
    try:
        cancha = Cancha.objects.get(id=cancha_id)
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        
        horarios = DisponibilidadService.obtener_horarios_disponibles(cancha, fecha_obj)
        
        return JsonResponse({
            'horarios': horarios,
            'mensaje': f'{len(horarios)} horarios disponibles'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ============ RF-07 & RF-08: GESTIÓN DE PAGOS ============

@login_required
def reserva_detalle(request, reserva_id):
    """Detalle de una reserva con opciones de pago"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar permisos
    if reserva.cliente != request.user and not es_recepcionista(request.user) and not es_admin(request.user):
        messages.error(request, 'No tienes permiso para ver esta reserva.')
        return redirect('cliente_dashboard')
    
    # Verificar si el pago en efectivo venció
    reserva.verifica_vencimiento_efectivo()
    
    pagos = reserva.pagos.all()
    
    context = {
        'reserva': reserva,
        'pagos': pagos,
        'pago_minimo': int(reserva.valor_total * 0.5),
        'metodos_pago': ['transferencia', 'tarjeta', 'efectivo'],
        'falta_pagar': reserva.get_falta_pagar()
    }
    return render(request, 'reservas/detalle.html', context)


@login_required
@require_http_methods(["POST"])
def registrar_pago(request, reserva_id):
    """Registra un pago para una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar permisos
    if reserva.cliente != request.user and not es_recepcionista(request.user):
        return JsonResponse({'error': 'Permiso denegado'}, status=403)
    
    try:
        monto = int(request.POST.get('monto', 0))
        metodo = request.POST.get('metodo')
        referencia = request.POST.get('referencia', '')
        
        # Validar monto
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        
        if monto > reserva.get_falta_pagar():
            raise ValueError(f"El monto no puede exceder lo faltante (${reserva.get_falta_pagar()})")
        
        # Validar pago mínimo
        if not PagoService.validar_pago_minimo(reserva.valor_pagado + monto, reserva.valor_total):
            minimo_requerido = int(reserva.valor_total * 0.5)
            raise ValueError(f"Pago mínimo requerido: ${minimo_requerido}")
        
        if metodo == 'efectivo':
            # Pago en efectivo con límite de 20 minutos
            PagoService.crear_pago_efectivo_temporal(reserva)
            pago = PagoService.crear_pago(reserva, monto, metodo, referencia)
            messages.success(request, f'Pago en efectivo registrado. Tiene 20 minutos para confirmar.')
        else:
            # Otros métodos
            pago = PagoService.crear_pago(reserva, monto, metodo, referencia)
            PagoService.confirmar_pago(pago)
            messages.success(request, 'Pago registrado exitosamente.')
        
        return redirect('reserva_detalle', reserva_id=reserva_id)
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('reserva_detalle', reserva_id=reserva_id)


# ============ RF-09: TARIFAS POR HORARIO ============
# Ya implementado en TarifaService.calcular_valor_reserva()


# ============ RF-10: GENERACIÓN DE FACTURAS ============

@login_required
def factura_detalle(request, factura_id):
    """Detalle de una factura"""
    factura = get_object_or_404(Factura, id=factura_id)
    
    # Verificar permisos
    if factura.cliente != request.user and not es_recepcionista(request.user) and not es_admin(request.user):
        messages.error(request, 'No tienes permiso para ver esta factura.')
        return redirect('/')
    
    return render(request, 'facturas/detalle.html', {'factura': factura})


# ============ RF-11: PUNTO DE VENTA (Recepcionista) ============

@login_required
@user_passes_test(es_recepcionista)
def pdv_nueva_venta(request):
    """Interfaz de punto de venta para crear una venta"""
    productos = Producto.objects.filter(stock__gt=0)
    
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        detalles_json = request.POST.get('detalles')
        
        try:
            detalles = json.loads(detalles_json)
            
            # Crear venta
            venta = Venta.objects.create(
                recepcionista=request.user,
                cliente_id=cliente_id if cliente_id else None,
                valor_total=0
            )
            
            valor_total = int(0)
            
            # Crear detalles
            for detalle in detalles:
                producto = Producto.objects.get(id=detalle['producto_id'])
                cantidad = int(detalle['cantidad'])
                precio_unitario = int(detalle['precio'])
                subtotal = precio_unitario * cantidad
                
                # Validar stock
                if producto.stock < cantidad:
                    raise ValueError(f"Stock insuficiente para {producto.nombre}")
                
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal
                )
                
                # Actualizar stock
                producto.stock -= cantidad
                producto.save()
                
                valor_total += subtotal
            
            # Actualizar total de venta
            venta.valor_total = valor_total
            venta.save()
            
            # Generar factura
            FacturaService.crear_factura_venta(venta)
            
            messages.success(request, f'Venta registrada. Factura generada.')
            return redirect('factura_detalle', factura_id=venta.factura.id)
        
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    # Obtener categorías para filtros
    categorias = productos.values('categoria').distinct()
    
    context = {
        'productos': productos,
        'categorias': categorias
    }
    return render(request, 'pdv/nueva_venta.html', context)


# ============ RF-12: CONSULTA DE FACTURAS ============

@login_required
def facturas_lista(request):
    """Lista de facturas según el rol del usuario"""
    if es_cliente(request.user):
        facturas = Factura.objects.filter(cliente=request.user)
    elif es_recepcionista(request.user):
        # Recepcionista ve todas las ventas que registró
        facturas = Factura.objects.filter(tipo='venta')
    elif es_admin(request.user):
        # Admin ve todas
        facturas = Factura.objects.all()
    else:
        facturas = Factura.objects.none()
    
    return render(request, 'facturas/lista.html', {'facturas': facturas})


# ============ RF-13: GESTIÓN DE PRODUCTOS (Admin) ============

@login_required
@user_passes_test(es_admin)
@login_required
@user_passes_test(es_admin)
@login_required
@user_passes_test(es_admin)
def admin_productos_list(request):
    """Lista de todos los productos"""
    productos = Producto.objects.all()
    return render(request, 'admin/productos/list.html', {'productos': productos})


@login_required
@user_passes_test(es_admin)
def admin_producto_crear(request):
    """Crea un nuevo producto"""
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('admin_productos_list')
        else:
            messages.error(request, 'Error al crear el producto.')
    else:
        form = ProductoForm()
    
    return render(request, 'admin/productos/crear.html', {
        'form': form,
        'categorias': Producto._meta.get_field('categoria').choices
    })


@login_required
@user_passes_test(es_admin)
def admin_producto_editar(request, producto_id):
    """Edita un producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('admin_productos_list')
        else:
            messages.error(request, 'Error al actualizar el producto.')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'admin/productos/editar.html', {
        'form': form,
        'producto': producto,
        'categorias': Producto._meta.get_field('categoria').choices
    })


@login_required
@user_passes_test(es_admin)
def admin_producto_eliminar(request, producto_id):
    """Elimina un producto de la base de datos"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre_producto}" eliminado correctamente.')
        return redirect('admin_productos_list')
    
    return render(request, 'admin/productos/confirmar_eliminar.html', {'producto': producto})


# ============ RF-14: GESTIÓN DE EMPLEADOS (Admin) ============

@login_required
@user_passes_test(es_admin)
def admin_empleados_list(request):
    """Lista de empleados (recepcionistas)"""
    empleados = UserRole.objects.filter(role__in=['recepcionista', 'administrador'])
    return render(request, 'admin/empleados/list.html', {'empleados': empleados})


@login_required
@user_passes_test(es_admin)
def admin_empleado_crear(request):
    """Crea un nuevo empleado (recepcionista)"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        password = request.POST.get('password')
        rol = request.POST.get('rol', 'recepcionista')
        
        try:
            if User.objects.filter(email__iexact=email).exists():
                raise ValueError('El correo electrónico ya está registrado.')
            
            # Crear usuario
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=nombre
            )
            
            # Crear rol
            UserRole.objects.create(
                user=user,
                role=rol
            )
            
            messages.success(request, 'Empleado creado exitosamente.')
            return redirect('admin_empleados_list')
        
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('admin_empleado_crear')
    
    return render(request, 'admin/empleados/crear.html', {
        'roles': [('recepcionista', 'Recepcionista'), ('administrador', 'Administrador')]
    })


@login_required
@user_passes_test(es_admin)
def admin_empleado_editar(request, empleado_id):
    """Edita un empleado"""
    role_profile = get_object_or_404(UserRole, id=empleado_id)
    user = role_profile.user
    
    if request.method == 'POST':
        user.first_name = request.POST.get('nombre')
        user.save()
        
        role_profile.role = request.POST.get('rol')
        role_profile.is_active = request.POST.get('is_active') == 'on'
        role_profile.save()
        
        messages.success(request, 'Empleado actualizado exitosamente.')
        return redirect('admin_empleados_list')
    
    context = {
        'role_profile': role_profile,
        'user': user,
        'roles': [('recepcionista', 'Recepcionista'), ('administrador', 'Administrador')]
    }
    return render(request, 'admin/empleados/editar.html', context)


@login_required
@user_passes_test(es_admin)
def admin_empleado_desactivar(request, empleado_id):
    """Desactiva un empleado"""
    role_profile = get_object_or_404(UserRole, id=empleado_id)
    
    if request.method == 'POST':
        role_profile.is_active = False
        role_profile.save()
        messages.success(request, 'Empleado desactivado.')
        return redirect('admin_empleados_list')
    
    return render(request, 'admin/empleados/confirmar_desactivar.html', {
        'role_profile': role_profile
    })


# ============ RF-15: DASHBOARD ADMINISTRATIVO ============

@login_required
@user_passes_test(es_admin)
def admin_dashboard(request):
    """Panel de administración con estadísticas"""
    # Periodo seleccionado
    periodo = request.GET.get('periodo', 'mes')  # dia, semana, mes
    
    # Calcular fechas
    hoy = timezone.now().date()
    if periodo == 'dia':
        fecha_inicio = hoy
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
    else:  # mes
        fecha_inicio = hoy - timedelta(days=30)
    
    # Estadísticas de ventas
    ventas = Venta.objects.filter(created_at__date__gte=fecha_inicio)
    total_ventas = ventas.aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    cantidad_ventas = ventas.count()
    
    # Estadísticas de reservas
    reservas = Reserva.objects.filter(created_at__date__gte=fecha_inicio)
    total_reservas_ingresos = reservas.aggregate(Sum('valor_pagado'))['valor_pagado__sum'] or 0
    cantidad_reservas = reservas.filter(estado='confirmada').count()
    
    # Canchas más utilizadas
    canchas_mas_usadas = Reserva.objects.filter(
        estado='confirmada',
        created_at__date__gte=fecha_inicio
    ).values('cancha__nombre').annotate(
        usos=Count('id')
    ).order_by('-usos')[:5]
    
    # Productos más vendidos
    productos_top = DetalleVenta.objects.filter(
        venta__created_at__date__gte=fecha_inicio
    ).values('producto__nombre').annotate(
        cantidad=Sum('cantidad'),
        ingresos=Sum('subtotal')
    ).order_by('-cantidad')[:5]
    
    # Estadísticas por día (últimos 30 días)
    estadisticas_diarias = []
    for i in range(30):
        dia = hoy - timedelta(days=i)
        ventas_dia = Venta.objects.filter(created_at__date=dia).aggregate(Sum('valor_total'))['valor_total__sum'] or 0
        reservas_dia = Reserva.objects.filter(
            estado='confirmada',
            created_at__date=dia
        ).aggregate(Sum('valor_pagado'))['valor_pagado__sum'] or 0
        
        estadisticas_diarias.append({
            'fecha': dia.strftime('%Y-%m-%d'),
            'ventas': float(ventas_dia),
            'reservas': float(reservas_dia),
            'total': float(ventas_dia + reservas_dia)
        })
    
    estadisticas_diarias.reverse()
    
    context = {
        'periodo': periodo,
        'total_ventas': float(total_ventas),
        'cantidad_ventas': cantidad_ventas,
        'total_reservas_ingresos': float(total_reservas_ingresos),
        'cantidad_reservas': cantidad_reservas,
        'total_ingresos': float(total_ventas + total_reservas_ingresos),
        'canchas_mas_usadas': list(canchas_mas_usadas),
        'productos_top': list(productos_top),
        'estadisticas_diarias': estadisticas_diarias,
    }
    
    return render(request, 'admin/dashboard.html', context)


# ============ DASHBOARDS POR ROL ============

@login_required
@user_passes_test(es_cliente)
def cliente_dashboard(request):
    """Dashboard para clientes"""
    reservas = Reserva.objects.filter(cliente=request.user).order_by('-created_at')[:10]
    facturas = Factura.objects.filter(cliente=request.user).order_by('-fecha_emision')[:10]
    
    context = {
        'reservas': reservas,
        'facturas': facturas,
        'total_gastado': Reserva.objects.filter(
            cliente=request.user,
            estado__in=['confirmada', 'completada']
        ).aggregate(Sum('valor_pagado'))['valor_pagado__sum'] or 0,
    }
    
    return render(request, 'cliente/dashboard.html', context)


@login_required
@user_passes_test(es_recepcionista)
def recepcionista_dashboard(request):
    """Dashboard para recepcionistas"""
    hoy = timezone.now().date()
    
    reservas_hoy = Reserva.objects.filter(fecha=hoy).order_by('hora_inicio')
    ventas_hoy = Venta.objects.filter(created_at__date=hoy)
    
    context = {
        'reservas_hoy': reservas_hoy,
        'ventas_hoy': ventas_hoy,
        'total_ventas_hoy': ventas_hoy.aggregate(Sum('valor_total'))['valor_total__sum'] or 0,
        'cantidad_reservas_hoy': reservas_hoy.filter(estado='confirmada').count(),
    }
    
    return render(request, 'recepcionista/dashboard.html', context)
