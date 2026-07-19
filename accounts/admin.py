"""
Configuración del admin para la app accounts.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin para el usuario personalizado."""

    list_display = ('username', 'first_name', 'last_name', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    fieldsets = UserAdmin.fieldsets + (
        ('Información del ERP', {'fields': ('role', 'telefono')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información del ERP', {'fields': ('role', 'telefono')}),
    )
