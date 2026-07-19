"""
Configuración del admin para la app clients.
"""

from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'documento', 'telefono', 'email', 'fecha_registro')
    search_fields = ('nombre', 'apellido', 'documento', 'email', 'telefono')
    list_filter = ('fecha_registro',)
