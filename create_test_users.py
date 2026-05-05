"""
Script para crear usuarios de prueba en Club1997
Uso: python manage.py shell < create_test_users.py
"""
from django.contrib.auth.models import User
from club1997.models import UserRole

# Datos de usuarios a crear
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

print("Creando usuarios de prueba...")

for user_data in test_users:
    email = user_data['email']
    password = user_data['password']
    first_name = user_data['first_name']
    last_name = user_data['last_name']
    role = user_data['role']
    
    # Verificar si el usuario ya existe
    if User.objects.filter(email=email).exists():
        print(f"⚠️  Usuario {email} ya existe. Omitiendo...")
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
                is_active=True,
                phone=user_data.get('phone', '')
            )
    
    print(f"✓ Usuario {email} creado como {role}")

print("\n✓ Usuarios de prueba creados exitosamente")
print("\nCuentas disponibles:")
print("Admin:       admin@club1997.com / admin123")
print("Recepción:   recepcion@club1997.com / recep123")
print("Cliente:     cliente@email.com / cliente123")
