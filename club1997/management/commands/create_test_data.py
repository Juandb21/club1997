from django.core.management.base import BaseCommand
from club1997.models import Cancha, TarifaHoraria
from decimal import Decimal


class Command(BaseCommand):
    help = 'Crear canchas y tarifas de ejemplo'

    def handle(self, *args, **options):
        self.stdout.write("Creando canchas y tarifas...")

        # Crear canchas
        canchas_data = [
            {
                'nombre': 'Cancha Fútbol 5 - Principal',
                'tipo': 'futbol5',
                'capacidad': 10,
                'descripcion': 'Cancha sintética profesional con iluminación',
                'estado': True
            },
            {
                'nombre': 'Cancha Fútbol 7 - Premium',
                'tipo': 'futbol7',
                'capacidad': 14,
                'descripcion': 'Cancha de primera calidad con grama sintética importada',
                'estado': True
            }
        ]

        canchas_creadas = []
        for cancha_data in canchas_data:
            cancha, created = Cancha.objects.get_or_create(
                nombre=cancha_data['nombre'],
                defaults={
                    'tipo': cancha_data['tipo'],
                    'capacidad': cancha_data['capacidad'],
                    'descripcion': cancha_data['descripcion'],
                    'estado': cancha_data['estado']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ Cancha creada: {cancha.nombre}"))
            else:
                self.stdout.write(f"⚠️  Cancha ya existe: {cancha.nombre}")
            canchas_creadas.append(cancha)

        # Crear tarifas por franja (en pesos colombianos)
        tarifas_data = [
            {'franja': 'mañana', 'precio': Decimal('30000')},    # 8am-12pm: $30,000
            {'franja': 'tarde', 'precio': Decimal('40000')},     # 12pm-6pm: $40,000
            {'franja': 'noche', 'precio': Decimal('50000')},     # 6pm-11pm: $50,000
        ]

        for cancha in canchas_creadas:
            self.stdout.write(f"\nConfigurando tarifas para: {cancha.nombre}")
            for tarifa_data in tarifas_data:
                tarifa, created = TarifaHoraria.objects.get_or_create(
                    cancha=cancha,
                    franja=tarifa_data['franja'],
                    defaults={'precio_por_hora': tarifa_data['precio']}
                )
                franja_display = dict(TarifaHoraria.FRANJA_CHOICES).get(tarifa_data['franja'])
                if created:
                    self.stdout.write(f"  ✓ {franja_display}: ${tarifa_data['precio']:,.0f} COP")
                else:
                    self.stdout.write(f"  ⚠️  {franja_display} ya existe")

        self.stdout.write(self.style.SUCCESS("\n✓ Canchas y tarifas configuradas exitosamente"))
