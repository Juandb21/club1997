from django.core.management.base import BaseCommand
from club1997.models import Producto
from decimal import Decimal


class Command(BaseCommand):
    help = 'Crear productos de ejemplo para el PDV'

    def handle(self, *args, **options):
        self.stdout.write("Creando productos de ejemplo...")

        productos_data = [
            # Bebidas
            {
                'nombre': 'Gaseosa 330ml',
                'categoria': 'bebida',
                'precio': Decimal('3000'),
                'stock': 50,
                'descripcion': 'Bebida refrescante'
            },
            {
                'nombre': 'Agua Embotellada',
                'categoria': 'bebida',
                'precio': Decimal('2000'),
                'stock': 100,
                'descripcion': 'Agua purificada'
            },
            {
                'nombre': 'Isotónico',
                'categoria': 'bebida',
                'precio': Decimal('5000'),
                'stock': 30,
                'descripcion': 'Bebida energética'
            },
            # Alimentos
            {
                'nombre': 'Hamburguesa',
                'categoria': 'alimento',
                'precio': Decimal('12000'),
                'stock': 20,
                'descripcion': 'Hamburguesa de carne'
            },
            {
                'nombre': 'Pizza por porción',
                'categoria': 'alimento',
                'precio': Decimal('8000'),
                'stock': 25,
                'descripcion': 'Pizza fresca'
            },
            {
                'nombre': 'Sándwich',
                'categoria': 'alimento',
                'precio': Decimal('10000'),
                'stock': 15,
                'descripcion': 'Sándwich variado'
            },
            {
                'nombre': 'Papas Fritas',
                'categoria': 'alimento',
                'precio': Decimal('5000'),
                'stock': 40,
                'descripcion': 'Papas fritas crujientes'
            },
            {
                'nombre': 'Barrita Energética',
                'categoria': 'alimento',
                'precio': Decimal('4000'),
                'stock': 35,
                'descripcion': 'Snack energético'
            },
        ]

        for producto_data in productos_data:
            producto, created = Producto.objects.get_or_create(
                nombre=producto_data['nombre'],
                defaults={
                    'categoria': producto_data['categoria'],
                    'precio': producto_data['precio'],
                    'stock': producto_data['stock'],
                    'descripcion': producto_data['descripcion'],
                    'estado': True
                }
            )
            categoria = dict(Producto.CATEGORIA_CHOICES).get(producto_data['categoria'])
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ {producto_data['nombre']} - ${producto_data['precio']:,.0f} ({categoria})"))
            else:
                self.stdout.write(f"⚠️  {producto_data['nombre']} ya existe")

        self.stdout.write(self.style.SUCCESS("\n✓ Productos creados exitosamente"))
