"""
Servicios y utilidades para la lógica de negocio del Club 1997
"""
from datetime import datetime, timedelta, time
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
from .models import Reserva, TarifaHoraria, Factura, Pago


class TarifaService:
    """Servicio para cálculos de tarifas"""
    
    @staticmethod
    def obtener_franja_horaria(hora: time) -> str:
        """Obtiene la franja horaria basada en la hora del día"""
        hora_int = hora.hour
        if 8 <= hora_int < 12:
            return 'mañana'
        elif 12 <= hora_int < 18:
            return 'tarde'
        elif 18 <= hora_int < 23:
            return 'noche'
        else:
            raise ValueError("Hora fuera del horario de operación (8:00 - 23:00)")
    
    @staticmethod
    def calcular_valor_reserva(cancha, fecha, hora_inicio, duracion_horas) -> Decimal:
        """
        Calcula el valor total de una reserva considerando 
        diferentes tarifas por franja horaria
        """
        valor_total = Decimal('0')
        
        for hora in range(duracion_horas):
            hora_actual = datetime.combine(fecha, hora_inicio)
            hora_actual = hora_actual + timedelta(hours=hora)
            
            franja = TarifaService.obtener_franja_horaria(hora_actual.time())
            
            tarifa = TarifaHoraria.objects.filter(
                cancha=cancha,
                franja=franja
            ).first()
            
            if tarifa:
                valor_total += tarifa.precio_por_hora
            else:
                raise ValueError(f"No hay tarifa configurada para {cancha} en franja {franja}")
        
        return valor_total
    
    @staticmethod
    def obtener_tarifa_por_franja(cancha, franja: str) -> Decimal:
        """Obtiene la tarifa de una cancha para una franja horaria específica"""
        tarifa = TarifaHoraria.objects.filter(
            cancha=cancha,
            franja=franja
        ).first()
        return tarifa.precio_por_hora if tarifa else None


class DisponibilidadService:
    """Servicio para verificar disponibilidad de canchas"""
    
    @staticmethod
    def verificar_disponibilidad(cancha, fecha, hora_inicio, duracion_horas) -> bool:
        """
        Verifica si una cancha está disponible en el horario solicitado.
        Retorna True si está disponible, False si hay conflicto.
        """
        from datetime import datetime, timedelta
        
        # Convertir a datetime para hacer comparaciones
        inicio = datetime.combine(fecha, hora_inicio)
        fin = inicio + timedelta(hours=duracion_horas)
        
        # Buscar reservas confirmadas en conflicto
        reservas_conflictivas = Reserva.objects.filter(
            cancha=cancha,
            fecha=fecha,
            estado__in=['confirmada', 'pendiente']
        ).exclude(estado='cancelada')
        
        for reserva in reservas_conflictivas:
            reserva_inicio = datetime.combine(reserva.fecha, reserva.hora_inicio)
            reserva_fin = reserva_inicio + timedelta(hours=reserva.duracion_horas)
            
            # Verificar solapamiento
            if not (fin <= reserva_inicio or inicio >= reserva_fin):
                return False
        
        return True
    
    @staticmethod
    def obtener_horarios_disponibles(cancha, fecha) -> list:
        """
        Retorna una lista de horas disponibles para una cancha en una fecha específica.
        Considera el horario de operación (8:00 - 23:00)
        """
        horarios_operacion = [(8, 23)]  # 8:00 a 23:00
        horas_disponibles = list(range(8, 23))
        
        # Obtener todas las reservas confirmadas para ese día
        reservas = Reserva.objects.filter(
            cancha=cancha,
            fecha=fecha,
            estado__in=['confirmada', 'pendiente']
        ).exclude(estado='cancelada')
        
        # Marcar horas ocupadas
        for reserva in reservas:
            hora_inicio = reserva.hora_inicio.hour
            duracion = reserva.duracion_horas
            for i in range(duracion):
                if hora_inicio + i in horas_disponibles:
                    horas_disponibles.remove(hora_inicio + i)
        
        return horas_disponibles


class PagoService:
    """Servicio para manejo de pagos"""
    
    @staticmethod
    def validar_pago_minimo(valor_pagado: Decimal, valor_total: Decimal) -> bool:
        """Valida que el pago sea al menos el 50% del total"""
        minimo_50_porciento = valor_total * Decimal('0.5')
        return valor_pagado >= minimo_50_porciento
    
    @staticmethod
    def crear_pago(reserva, monto: Decimal, metodo: str, referencia: str = None, estado: str = 'pendiente_aceptacion') -> Pago:
        """Crea un registro de pago para una reserva"""
        pago = Pago.objects.create(
            reserva=reserva,
            monto=monto,
            metodo=metodo,
            referencia=referencia,
            estado=estado
        )
        return pago
    
    @staticmethod
    def confirmar_pago(pago: Pago):
        """Confirma un pago y actualiza el estado de la reserva si aplica"""
        pago.estado = 'confirmado'
        pago.save()
        
        # Actualizar valor pagado en la reserva
        reserva = pago.reserva
        reserva.valor_pagado += pago.monto
        reserva.save()
        
        # Si se ha pagado al menos el 50%, cambiar estado a confirmada
        if reserva.valor_pagado >= (reserva.valor_total * Decimal('0.5')):
            if reserva.estado == 'pendiente':
                reserva.estado = 'confirmada'
                reserva.metodo_pago = pago.metodo
                reserva.save()
    
    @staticmethod
    def crear_pago_efectivo_temporal(reserva):
        """
        Crea una reserva temporal con pago en efectivo.
        El pago debe realizarse en máximo 20 minutos.
        """
        reserva.metodo_pago = 'efectivo'
        reserva.fecha_vencimiento_efectivo = timezone.now() + timedelta(minutes=20)
        reserva.estado = 'pendiente'
        reserva.save()
    
    @staticmethod
    def procesar_vencimiento_efectivo():
        """
        Cancela las reservas con pago en efectivo que venció.
        Debería ejecutarse periódicamente (ej: tarea programada)
        """
        reservas_efectivo = Reserva.objects.filter(
            metodo_pago='efectivo',
            estado='pendiente',
            fecha_vencimiento_efectivo__isnull=False
        )
        
        canceladas = 0
        for reserva in reservas_efectivo:
            if reserva.verifica_vencimiento_efectivo():
                canceladas += 1
        
        return canceladas


class FacturaService:
    """Servicio para generación de facturas"""
    
    @staticmethod
    def generar_numero_factura() -> str:
        """Genera un número de factura único"""
        from django.utils.timezone import now
        timestamp = now().strftime("%Y%m%d%H%M%S")
        numero = Factura.objects.count() + 1
        return f"FAC-{timestamp}-{numero}"
    
    @staticmethod
    def crear_factura_reserva(reserva) -> Factura:
        """Crea una factura para una reserva"""
        numero = FacturaService.generar_numero_factura()
        
        descripcion = f"Reserva de {reserva.cancha.nombre}\n"
        descripcion += f"Fecha: {reserva.fecha}\n"
        descripcion += f"Hora: {reserva.hora_inicio} - {reserva.get_hora_fin()}\n"
        descripcion += f"Duración: {reserva.duracion_horas} hora(s)\n"
        
        factura = Factura.objects.create(
            numero_factura=numero,
            tipo='reserva',
            cliente=reserva.cliente,
            reserva=reserva,
            valor_total=reserva.valor_total,
            descripcion=descripcion
        )
        return factura
    
    @staticmethod
    def crear_factura_venta(venta) -> Factura:
        """Crea una factura para una venta"""
        numero = FacturaService.generar_numero_factura()
        
        descripcion = "Venta de productos\n"
        for detalle in venta.detalles.all():
            descripcion += f"- {detalle.producto.nombre} x{detalle.cantidad}: ${detalle.subtotal}\n"
        
        factura = Factura.objects.create(
            numero_factura=numero,
            tipo='venta',
            cliente=venta.cliente,
            venta=venta,
            valor_total=venta.valor_total,
            descripcion=descripcion
        )
        return factura


class ReservaService:
    """Servicio para manejo de reservas"""
    
    @staticmethod
    def crear_reserva(cliente, cancha, fecha, hora_inicio, duracion_horas) -> Reserva:
        """
        Crea una nueva reserva validando disponibilidad y calculando tarifa.
        Retorna la reserva o lanza excepción si no es posible.
        """
        # Validar que sea mínimo 1 hora
        if duracion_horas < 1:
            raise ValueError("La duración mínima es de 1 hora")
        
        # Validar disponibilidad
        if not DisponibilidadService.verificar_disponibilidad(cancha, fecha, hora_inicio, duracion_horas):
            raise ValueError("La cancha no está disponible en el horario solicitado")
        
        # Calcular valor
        valor_total = TarifaService.calcular_valor_reserva(
            cancha, fecha, hora_inicio, duracion_horas
        )
        
        # Crear reserva
        reserva = Reserva.objects.create(
            cliente=cliente,
            cancha=cancha,
            fecha=fecha,
            hora_inicio=hora_inicio,
            duracion_horas=duracion_horas,
            valor_total=valor_total,
            estado='pendiente'
        )
        
        return reserva
    
    @staticmethod
    def confirmar_reserva(reserva):
        """Confirma una reserva que ha cumplido con el pago mínimo"""
        if reserva.es_pago_incompleto():
            raise ValueError(f"Falta pagar ${reserva.get_falta_pagar()}")
        
        reserva.estado = 'confirmada'
        reserva.save()
        
        # Generar factura
        FacturaService.crear_factura_reserva(reserva)
    
    @staticmethod
    def cancelar_reserva(reserva, motivo: str = None):
        """Cancela una reserva"""
        reserva.estado = 'cancelada'
        reserva.save()
