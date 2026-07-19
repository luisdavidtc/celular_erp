"""
Configuración del admin para la app inventory.
"""

from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'categoria', 'precio_venta', 'stock', 'stock_minimo')
    list_filter = ('categoria', 'marca')
    search_fields = ('nombre', 'codigo', 'codigo_barras', 'marca', 'modelo')
