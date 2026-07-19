"""
Configuración de URLs principal para el proyecto erp_config.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('cuentas/', include('accounts.urls')),
    path('clientes/', include('clients.urls')),
    path('inventario/', include('inventory.urls')),
    path('ventas/', include('sales.urls')),
    path('servicio/', include('repairs.urls')),
    path('configuracion/', include('company.urls')),
]

# Servir archivos de medios en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
