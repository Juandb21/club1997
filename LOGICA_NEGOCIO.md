# Club 1997 - Sistema de Gestión de Canchas

Sistema web completo para la gestión de una cancha sintética con reservas, pagos, facturación, ventas de productos y reportes.

## Estructura Implementada

### Modelos de Base de Datos (models.py)
- **UserRole**: Modelo de roles de usuario (cliente, recepcionista, administrador)
- **Cancha**: Gestión de canchas (Fútbol 5 y Fútbol 7)
- **TarifaHoraria**: Tarifas por franja horaria (mañana, tarde, noche)
- **Reserva**: Sistema de reservas con cálculo automático de tarifas
- **Producto**: Catálogo de productos (alimentos y bebidas)
- **Venta**: Registro de ventas en PDV
- **DetalleVenta**: Detalles de productos en ventas
- **Factura**: Generación automática de facturas
- **Pago**: Registro de pagos con múltiples métodos

### Servicios de Lógica de Negocio (services.py)

#### TarifaService
- `obtener_franja_horaria()`: Identifica la franja horaria basada en la hora
- `calcular_valor_reserva()`: Calcula el costo considerando tarifas por franja
- `obtener_tarifa_por_franja()`: Obtiene tarifa específica

#### DisponibilidadService
- `verificar_disponibilidad()`: Valida que no haya conflictos de horarios
- `obtener_horarios_disponibles()`: Lista horarios libres para un día

#### PagoService
- `validar_pago_minimo()`: Verifica el pago mínimo del 50%
- `crear_pago()`: Registra un pago
- `confirmar_pago()`: Confirma y actualiza reserva
- `crear_pago_efectivo_temporal()`: Crea pago en efectivo con límite de 20 min

#### FacturaService
- `generar_numero_factura()`: Crea número único
- `crear_factura_reserva()`: Genera factura para reserva
- `crear_factura_venta()`: Genera factura para venta

#### ReservaService
- `crear_reserva()`: Crea reserva con validaciones
- `confirmar_reserva()`: Confirma si cumple con pago mínimo
- `cancelar_reserva()`: Cancela reserva

### Vistas (views.py) - 15 Requisitos Funcionales

**RF-01**: Página de inicio
- `home_view()`: Muestra información del club, canchas, horarios y tarifas

**RF-02**: Registro de usuarios
- `register_view()`: Registro de clientes con validación de email único

**RF-03**: Inicio de sesión
- `login_view()`: Autenticación con redirección según rol
- `logout_view()`: Cierre de sesión

**RF-04**: Gestión de canchas (Admin)
- `admin_canchas_list()`: Lista todas las canchas
- `admin_cancha_crear()`: Crea nueva cancha
- `admin_cancha_editar()`: Edita cancha
- `admin_cancha_tarifas()`: Configura tarifas por franja
- `admin_cancha_eliminar()`: Desactiva cancha

**RF-05 & RF-06**: Creación y disponibilidad de reservas
- `reserva_crear()`: Crea reserva con validación
- `verificar_disponibilidad_api()`: API AJAX para disponibilidad
- `horarios_disponibles_api()`: API AJAX para horarios libres

**RF-07 & RF-08**: Gestión de pagos
- `reserva_detalle()`: Muestra detalles y opciones de pago
- `registrar_pago()`: Registra pago (con manejo de efectivo temporal)

**RF-09**: Tarifas por horario (implementado en TarifaService)

**RF-10**: Generación de facturas
- `factura_detalle()`: Muestra factura generada

**RF-11**: Punto de venta
- `pdv_nueva_venta()`: Interfaz de venta de productos

**RF-12**: Consulta de facturas
- `facturas_lista()`: Lista facturas según rol

**RF-13**: Gestión de productos (Admin)
- `admin_productos_list()`: Lista productos
- `admin_producto_crear()`: Crea producto
- `admin_producto_editar()`: Edita producto
- `admin_producto_eliminar()`: Desactiva producto

**RF-14**: Gestión de empleados (Admin)
- `admin_empleados_list()`: Lista empleados
- `admin_empleado_crear()`: Crea recepcionista/admin
- `admin_empleado_editar()`: Edita empleado
- `admin_empleado_desactivar()`: Desactiva empleado

**RF-15**: Dashboard administrativo
- `admin_dashboard()`: Panel con estadísticas (ventas, reservas, canchas, productos)

**Dashboards por rol**:
- `cliente_dashboard()`: Dashboard para clientes
- `recepcionista_dashboard()`: Dashboard para recepcionistas

### Rutas (urls.py)

Todas las rutas están configuradas y mapeadas según las funcionalidades.

### Formularios (forms.py)

- `ReservaForm`: Validación de reservas
- `PagoForm`: Registro de pagos
- `CanchaForm`: Gestión de canchas
- `TarifaForm`: Configuración de tarifas
- `ProductoForm`: Gestión de productos
- `EmpleadoForm`: Gestión de empleados
- `VentaForm`: Creación de ventas

## Instalación y Configuración

### 1. Crear migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Crear superusuario administrador

```bash
python manage.py createsuperuser
```

Luego, desde el panel de administración Django, editar el superusuario y asignarle un `UserRole` con role='administrador'.

### 3. Ejecutar servidor

```bash
python manage.py runserver
```

### 4. Acceder al sistema

- **Home**: http://localhost:8000/
- **Registro**: http://localhost:8000/register/
- **Login**: http://localhost:8000/login/
- **Admin Panel**: http://localhost:8000/admin/

## Restricciones de Negocio Implementadas

✅ Pago mínimo del 50%
✅ Tiempo mínimo de reserva: 1 hora
✅ Pago en efectivo con límite de 20 minutos (con vencimiento automático)
✅ Tarifas dinámicas por franja horaria
✅ Disponibilidad en tiempo real
✅ Validación de emails únicos
✅ Control de roles y permisos
✅ Generación automática de facturas
✅ Control de stock de productos

## Próximos Pasos

Los mockups de interfaz deben implementarse en los siguientes templates:

### Templates a crear:
- `home.html`: Página de inicio
- `register.html`: Registro de usuarios
- `login.html`: Login
- `cliente/dashboard.html`: Dashboard cliente
- `recepcionista/dashboard.html`: Dashboard recepcionista
- `admin/dashboard.html`: Dashboard administrativo
- `admin/canchas/list.html`, `crear.html`, `editar.html`, `tarifas.html`
- `admin/productos/list.html`, `crear.html`, `editar.html`
- `admin/empleados/list.html`, `crear.html`, `editar.html`
- `reservas/crear.html`, `detalle.html`
- `facturas/list.html`, `detalle.html`
- `pdv/nueva_venta.html`

Todos los templates deben incluir:
- CSS personalizado
- JavaScript para validaciones y APIs AJAX
- Responsive design

---

**Desarrollado para Club 1997 - Mayo 2026**
