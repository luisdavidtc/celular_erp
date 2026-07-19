from django.apps import AppConfig


class CompanyConfig(AppConfig):
    """Configuración de la app company (Configuración de Empresa)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'company'
    verbose_name = 'Configuración de Empresa'
