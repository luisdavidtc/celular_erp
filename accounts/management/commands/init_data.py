"""
Comando de gestión para crear los datos iniciales del ERP.

Crea:
- Un superusuario administrador por defecto (admin / admin123)
- Categorías de ejemplo (Smartphones, Accesorios, Repuestos)

Uso:
    python manage.py init_data
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from inventory.models import Category

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea el superusuario administrador por defecto y categorías de ejemplo.'

    def handle(self, *args, **options):
        # --- Superusuario administrador ---
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@celulares-erp.com',
                password='admin123',
                first_name='Administrador',
                last_name='General',
                role=User.Roles.ADMIN,
            )
            self.stdout.write(self.style.SUCCESS('✔ Superusuario "admin" creado (contraseña: admin123).'))
        else:
            self.stdout.write(self.style.WARNING('• El usuario "admin" ya existe; se omite.'))

        # --- Categorías de ejemplo ---
        categorias = [
            ('Smartphones', 'Teléfonos inteligentes de todas las marcas.'),
            ('Accesorios', 'Fundas, cargadores, audífonos y otros accesorios.'),
            ('Repuestos', 'Pantallas, baterías y componentes para reparación.'),
        ]
        creadas = 0
        for nombre, descripcion in categorias:
            categoria, creada = Category.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion},
            )
            if creada:
                creadas += 1
        self.stdout.write(self.style.SUCCESS(f'✔ Categorías de ejemplo: {creadas} creadas, {len(categorias) - creadas} ya existían.'))

        self.stdout.write(self.style.SUCCESS('\n¡Datos iniciales cargados correctamente!'))
