# create_dev_admin.py
import os
import django
from django.core.management.base import BaseCommand

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'w1.settings')
django.setup()

from core.models import User

class Command(BaseCommand):
    help = 'Cria um superusuário para desenvolvimento'

    def handle(self, *args, **options):
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'diogo232musso@gmail.com')
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin12345678')
        admin_first_name = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Diogo')
        admin_last_name = os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'Coutinho')

        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
                first_name=admin_first_name,
                last_name=admin_last_name,
                user_type='admin'
            )
            self.stdout.write(self.style.SUCCESS(
                f"Superusuário '{admin_email}' criado com sucesso!"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"Superusuário '{admin_email}' já existe."
            ))

if __name__ == '__main__':
    Command().handle()