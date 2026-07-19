"""
Context processor de la app company.

Inyecta la configuración de empresa (nombre comercial, logo, colores)
en todos los templates, para que el layout base (sidebar, navbar) pueda
usarla sin que cada vista tenga que consultarla manualmente.
"""

from django.db.utils import OperationalError, ProgrammingError

from .models import Company


def company_context(request):
    """Agrega `company_config` y `branding_config` al contexto de cada template.

    Se protege con try/except porque este processor se ejecuta en cada
    request, incluyendo antes de aplicar migraciones (por ejemplo, en un
    entorno recién clonado) donde la tabla `company_company` aún no existe.
    """
    try:
        company = Company.get_solo()
        branding = getattr(company, 'identidad_visual', None)
    except (OperationalError, ProgrammingError):
        company = None
        branding = None

    return {
        'company_config': company,
        'branding_config': branding,
    }
