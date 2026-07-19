"""
Configuración del admin para la app sales.
"""

from django.contrib import admin

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'vendedor', 'fecha', 'total', 'ganancia', 'estado')
    list_filter = ('estado', 'fecha')
    search_fields = ('cliente__nombre', 'cliente__apellido', 'cliente__documento')
    date_hierarchy = 'fecha'
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('producto__nombre',)
