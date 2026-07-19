"""
Modelos de la app accounts.

Define el usuario personalizado con roles para el ERP.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Usuario personalizado con un campo de rol."""

    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        VENDEDOR = 'vendedor', 'Vendedor'
        TECNICO = 'tecnico', 'Técnico'

    role = models.CharField(
        'Rol',
        max_length=20,
        choices=Roles.choices,
        default=Roles.VENDEDOR,
    )
    telefono = models.CharField('Teléfono', max_length=30, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def es_admin(self):
        """Indica si el usuario es administrador (rol o superusuario)."""
        return self.role == self.Roles.ADMIN or self.is_superuser
