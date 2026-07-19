"""
Configuración del admin para la app repairs.
"""

from django.contrib import admin

from .models import RepairOrder, RepairPart


class RepairPartInline(admin.TabularInline):
    model = RepairPart
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(RepairOrder)
class RepairOrderAdmin(admin.ModelAdmin):
    list_display = ('numero_orden', 'cliente', 'equipo', 'tecnico', 'estado', 'total', 'venta', 'fecha_recepcion')
    list_filter = ('estado', 'fecha_recepcion')
    search_fields = ('numero_orden', 'cliente__nombre', 'cliente__apellido', 'imei', 'equipo')
    date_hierarchy = 'fecha_recepcion'
    inlines = [RepairPartInline]
    # De solo lectura: la venta se asigna únicamente a través de
    # RepairOrder.facturar() (botón "Facturar" en el detalle de la orden),
    # nunca manualmente, para no saltarse la validación de doble
    # facturación ni dejar la venta sin sus ítems/consecutivo.
    readonly_fields = ('venta',)


@admin.register(RepairPart)
class RepairPartAdmin(admin.ModelAdmin):
    list_display = ('orden', 'descripcion', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('descripcion',)
