# create_dev_admin.py
import os
import django
from django.contrib.auth.hashers import make_password

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'w1.settings')
django.setup()

# Agora você pode importar seus modelos
from core.models import User # Use o caminho correto para seu modelo User

def create_admin_user():
    ADMIN_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'senha') # Pega da env var se existir

    if not User.objects.filter(email=ADMIN_EMAIL).exists():
        User.objects.create(
            email=ADMIN_EMAIL,
            password=make_password(ADMIN_PASSWORD),
            user_type='admin',
            is_superuser=True,
            is_staff=True,
            is_active=True,
            first_name='Dev',
            last_name='Admin'
        )
        print(f"Usuário admin '{ADMIN_EMAIL}' criado com senha '{ADMIN_PASSWORD}' (AVISO: senha insegura!).")
    else:
        print(f"Usuário admin '{ADMIN_EMAIL}' já existe.")

if __name__ == '__main__':
    create_admin_user()