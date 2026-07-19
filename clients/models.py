"""
Modelos de la app clients.
"""

from django.db import models


class Client(models.Model):
    """Cliente de la empresa."""

    nombre = models.CharField('Nombre', max_length=100)
    apellido = models.CharField('Apellido', max_length=100)
    documento = models.CharField('Documento (cédula)', max_length=30, unique=True)
    telefono = models.CharField('Teléfono', max_length=30, blank=True)
    email = models.EmailField('Correo electrónico', blank=True)
    direccion = models.CharField('Dirección', max_length=255, blank=True)
    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre', 'apellido']

    def __str__(self):
        return f'{self.nombre} {self.apellido} ({self.documento})'

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'
