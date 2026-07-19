"""
Vistas de la app dashboard: panel principal con KPIs reales.
"""

import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone

from inventory.models import Product
from repairs.models import RepairOrder
from sales.models import Sale


def _formato_moneda(valor):
    """Formatea un valor decimal como moneda colombiana."""
    valor = valor or Decimal('0')
    return '$ ' + f'{int(valor):,}'.replace(',', '.')


@login_required
def index(request):
    """Panel principal del ERP con indicadores clave (KPIs) reales."""
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)

    completadas = Sale.objects.filter(estado=Sale.Estado.COMPLETADA)

    # Ventas del día (suma de ventas completadas hoy)
    ventas_dia = completadas.filter(fecha__date=hoy).aggregate(t=Sum('total'))['t'] or Decimal('0')

    # Ventas del mes (suma del mes actual)
    ventas_mes = completadas.filter(fecha__date__gte=inicio_mes).aggregate(t=Sum('total'))['t'] or Decimal('0')

    # Ganancia del mes
    ganancia_mes = completadas.filter(fecha__date__gte=inicio_mes).aggregate(t=Sum('ganancia'))['t'] or Decimal('0')

    # Equipos en reparación (órdenes que no están entregadas)
    equipos_reparacion = RepairOrder.objects.exclude(estado=RepairOrder.Estado.ENTREGADO).count()

    # Inventario bajo (productos con stock <= stock_minimo)
    productos_bajo_stock = Product.objects.filter(stock__lte=F('stock_minimo')).count()

    # Facturas emitidas (total de ventas completadas)
    facturas_emitidas = completadas.count()

    kpis = [
        {'label': 'Ventas del día', 'valor': _formato_moneda(ventas_dia), 'icono': 'bi-cart-check', 'color': '#2563eb'},
        {'label': 'Ventas del mes', 'valor': _formato_moneda(ventas_mes), 'icono': 'bi-graph-up-arrow', 'color': '#16a34a'},
        {'label': 'Ganancia del mes', 'valor': _formato_moneda(ganancia_mes), 'icono': 'bi-cash-stack', 'color': '#9333ea'},
        {'label': 'Equipos en reparación', 'valor': str(equipos_reparacion), 'icono': 'bi-tools', 'color': '#ea580c'},
        {'label': 'Inventario bajo', 'valor': str(productos_bajo_stock), 'icono': 'bi-exclamation-triangle', 'color': '#ca8a04'},
        {'label': 'Facturas emitidas', 'valor': str(facturas_emitidas), 'icono': 'bi-receipt', 'color': '#0891b2'},
    ]

    # Gráfico: ventas de los últimos 7 días
    etiquetas = []
    datos_ventas = []
    nombres_dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        total_dia = completadas.filter(fecha__date=dia).aggregate(t=Sum('total'))['t'] or Decimal('0')
        etiquetas.append(f'{nombres_dias[dia.weekday()]} {dia.day}')
        datos_ventas.append(float(total_dia))

    contexto = {
        'kpis': kpis,
        'grafico_labels': json.dumps(etiquetas),
        'grafico_datos': json.dumps(datos_ventas),
        'seccion_activa': 'dashboard',
    }
    return render(request, 'dashboard/index.html', contexto)
