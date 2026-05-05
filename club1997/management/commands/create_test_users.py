from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from club1997.models import UserRole


class Command(BaseCommand):
    help = 'Crear usuarios de prueba para Club1997'

    def handle(self, *args, **options):
        test_users = [
            {
                'email': 'admin@club1997.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'Club',
                'role': 'administrador'
            },
            {
                'email': 'recepcion@club1997.com',
                'password': 'recep123',
                'first_name': 'Recepcionista',
                'last_name': 'Club',
                'role': 'recepcionista'
            },
            {
                'email': 'cliente@email.com',
                'password': 'cliente123',
                'first_name': 'Cliente',
                'last_name': 'Demo',
                'role': 'cliente'
            }
        ]

        self.stdout.write("Creando usuarios de prueba...")

        for user_data in test_users:
            email = user_data['email']
            password = user_data['password']
            first_name = user_data['first_name']
            last_name = user_data['last_name']
            role = user_data['role']
            
            # Verificar si el usuario ya existe
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"⚠️  Usuario {email} ya existe. Omitiendo...")
                continue
            
            # Crear usuario
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Crear perfil de rol
            UserRole.objects.create(
                user=user,
                role=role,
                is_active=True
            )
            
            self.stdout.write(self.style.SUCCESS(f'✓ Usuario {email} creado como {role}'))

        self.stdout.write(self.style.SUCCESS("\n✓ Usuarios de prueba creados exitosamente"))
