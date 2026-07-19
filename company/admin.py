from django.contrib import admin

from .models import (
    BrandingSettings,
    Company,
    EmailSettings,
    InvoiceSettings,
    PrintSettings,
    SalesSettings,
    WhatsAppSettings,
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('nombre_comercial', 'nit', 'estado', 'activo', 'fecha_modificacion')


admin.site.register(BrandingSettings)
admin.site.register(InvoiceSettings)
admin.site.register(SalesSettings)
admin.site.register(PrintSettings)
admin.site.register(WhatsAppSettings)
admin.site.register(EmailSettings)
