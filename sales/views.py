"""
Vistas de la app sales (Ventas).

Incluye:
- Creación de venta con formulario dinámico (ítems vía JS).
- Endpoints JSON para autocompletado de clientes y productos.
- Listado con filtros por fecha y estado.
- Detalle de venta.
- Anulación de venta (devuelve stock).
"""

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from clients.models import Client
from company.utils import generar_qr_data_uri, obtener_configuracion_empresa
from inventory.models import Product

from .forms import SaleForm
from .models import Sale, SaleItem

# Roles que pueden gestionar ventas
ROLES_VENTAS = ('admin', 'vendedor')


def _to_decimal(valor, por_defecto='0'):
    """Convierte un valor a Decimal de forma segura."""
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(por_defecto)


# ===================== Endpoints JSON (autocomplete) =====================

@login_required
def client_search(request):
    """Búsqueda de clientes para autocompletado (JSON)."""
    q = request.GET.get('q', '').strip()
    clientes = Client.objects.all()
    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q)
            | Q(apellido__icontains=q)
            | Q(documento__icontains=q)
            | Q(telefono__icontains=q)
        )
    clientes = clientes[:15]
    data = [
        {
            'id': c.id,
            'nombre': c.nombre_completo,
            'documento': c.documento,
            'telefono': c.telefono,
        }
        for c in clientes
    ]
    return JsonResponse({'resultados': data})


@login_required
def product_search(request):
    """Búsqueda de productos para autocompletado (JSON)."""
    q = request.GET.get('q', '').strip()
    productos = Product.objects.all()
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q)
            | Q(codigo__icontains=q)
            | Q(codigo_barras__icontains=q)
            | Q(marca__icontains=q)
            | Q(modelo__icontains=q)
        )
    productos = productos[:15]
    data = [
        {
            'id': p.id,
            'nombre': p.nombre,
            'codigo': p.codigo,
            'precio_venta': str(p.precio_venta),
            'precio_compra': str(p.precio_compra),
            'stock': p.stock,
        }
        for p in productos
    ]
    return JsonResponse({'resultados': data})


# ===================== CRUD Ventas =====================

@login_required
@role_required(*ROLES_VENTAS)
def sale_list(request):
    """Lista de ventas con filtros por fecha y estado."""
    estado = request.GET.get('estado', '').strip()
    fecha_desde = request.GET.get('desde', '').strip()
    fecha_hasta = request.GET.get('hasta', '').strip()

    ventas = Sale.objects.select_related('cliente', 'vendedor').all()
    if estado:
        ventas = ventas.filter(estado=estado)
    if fecha_desde:
        ventas = ventas.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        ventas = ventas.filter(fecha__date__lte=fecha_hasta)

    contexto = {
        'ventas': ventas,
        'estado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estados': Sale.Estado.choices,
        'seccion_activa': 'ventas',
    }
    return render(request, 'sales/sale_list.html', contexto)


@login_required
@role_required(*ROLES_VENTAS)
def sale_create(request):
    """Crear una nueva venta con ítems dinámicos."""
    if request.method == 'POST':
        form = SaleForm(request.POST)
        # Recolectar ítems enviados en arrays paralelos
        producto_ids = request.POST.getlist('producto_id')
        cantidades = request.POST.getlist('cantidad')
        precios = request.POST.getlist('precio_unitario')
        descuentos = request.POST.getlist('descuento_item')

        if not producto_ids:
            messages.error(request, 'Debes agregar al menos un producto a la venta.')
            return render(request, 'sales/sale_form.html', {
                'form': form, 'titulo': 'Nueva venta', 'seccion_activa': 'ventas',
            })

        if form.is_valid():
            try:
                with transaction.atomic():
                    venta = form.save(commit=False)
                    venta.vendedor = request.user
                    venta.estado = Sale.Estado.COMPLETADA
                    venta.save()
                    # Asigna el consecutivo de facturación al confirmar la venta.
                    # select_for_update() dentro del método bloquea la fila de
                    # InvoiceSettings para que dos ventas concurrentes nunca
                    # reciban el mismo número.
                    venta.asignar_numero_factura()

                    for idx, prod_id in enumerate(producto_ids):
                        if not prod_id:
                            continue
                        producto = get_object_or_404(Product, pk=prod_id)
                        cantidad = int(cantidades[idx]) if idx < len(cantidades) and cantidades[idx] else 0
                        if cantidad <= 0:
                            continue

                        # Validar stock disponible
                        if cantidad > producto.stock:
                            raise ValueError(
                                f'Stock insuficiente para "{producto.nombre}". '
                                f'Disponible: {producto.stock}, solicitado: {cantidad}.'
                            )

                        precio = _to_decimal(precios[idx]) if idx < len(precios) else producto.precio_venta
                        desc = _to_decimal(descuentos[idx]) if idx < len(descuentos) else Decimal('0')

                        item = SaleItem(
                            venta=venta,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio,
                            precio_compra=producto.precio_compra,
                            descuento=desc,
                        )
                        item.save()

                        # Descontar stock
                        producto.stock -= cantidad
                        producto.save(update_fields=['stock'])

                    # Recalcular totales en el servidor (fuente de verdad)
                    venta.recalcular()

                messages.success(request, f'Venta {venta.numero} registrada correctamente.')
                return redirect('sales:sale_detail', pk=venta.pk)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = SaleForm()

    contexto = {
        'form': form,
        'titulo': 'Nueva venta',
        'seccion_activa': 'ventas',
    }
    return render(request, 'sales/sale_form.html', contexto)


@login_required
@role_required(*ROLES_VENTAS)
def sale_detail(request, pk):
    """Detalle de una venta."""
    venta = get_object_or_404(
        Sale.objects.select_related('cliente', 'vendedor'), pk=pk
    )
    config = obtener_configuracion_empresa()
    contexto = {
        'venta': venta,
        'items': venta.items.select_related('producto').all(),
        'facturacion': config['facturacion'],
        'ventas_cfg': config['ventas_cfg'],
        # Si la venta viene de una orden de servicio técnico y la
        # configuración no pide desglose, se muestra un único concepto
        # agrupado en vez de los ítems de mano de obra/repuestos por
        # separado (los ítems siguen existiendo para inventario/utilidad).
        'agrupar_servicio_tecnico': (
            hasattr(venta, 'orden_servicio')
            and not config['ventas_cfg'].mostrar_desglose_servicio_tecnico
        ),
        'seccion_activa': 'ventas',
    }
    return render(request, 'sales/sale_detail.html', contexto)


@login_required
@role_required(*ROLES_VENTAS)
def sale_print(request, pk):
    """Comprobante de venta imprimible (ticket térmico o factura tamaño carta).

    Usa los datos de Configuración de Empresa (identidad visual, facturación,
    ventas e impresión) para armar el documento, sin depender del layout
    general del ERP.
    """
    venta = get_object_or_404(
        Sale.objects.select_related('cliente', 'vendedor'), pk=pk
    )
    config = obtener_configuracion_empresa()
    empresa = config['empresa']
    impresion = config['impresion']

    qr_contenido = None
    if impresion.mostrar_qr:
        referencia = (
            f'{config["facturacion"].prefijo_facturacion}-{venta.numero_factura}'
            if venta.numero_factura else venta.numero
        )
        qr_contenido = (
            f'Factura {referencia} | {empresa.nombre_comercial or empresa.razon_social} '
            f'| NIT {empresa.nit} | Total: {empresa.simbolo_moneda}{venta.total} '
            f'| Fecha: {venta.fecha:%d/%m/%Y %H:%M}'
        )

    contexto = {
        'venta': venta,
        'items': venta.items.select_related('producto').all(),
        'agrupar_servicio_tecnico': (
            hasattr(venta, 'orden_servicio')
            and not config['ventas_cfg'].mostrar_desglose_servicio_tecnico
        ),
        'empresa': empresa,
        'branding': config['branding'],
        'facturacion': config['facturacion'],
        'ventas_cfg': config['ventas_cfg'],
        'impresion': impresion,
        'qr_data_uri': generar_qr_data_uri(qr_contenido),
    }
    return render(request, 'sales/sale_print.html', contexto)


@login_required
@role_required(*ROLES_VENTAS)
def sale_void(request, pk):
    """Anular una venta y devolver el stock."""
    venta = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        if venta.estado == Sale.Estado.ANULADA:
            messages.warning(request, 'La venta ya está anulada.')
            return redirect('sales:sale_detail', pk=venta.pk)

        with transaction.atomic():
            # Si la venta fue generada automáticamente al facturar una
            # reparación (ver RepairOrder.facturar), sus repuestos ya
            # fueron descontados del stock al usarse en la orden de
            # servicio (no al facturar). Devolver stock aquí duplicaría
            # esa devolución incorrectamente, así que se omite.
            if not hasattr(venta, 'orden_servicio'):
                # Devolver stock de cada ítem
                for item in venta.items.select_related('producto').all():
                    producto = item.producto
                    producto.stock += item.cantidad
                    producto.save(update_fields=['stock'])
            venta.estado = Sale.Estado.ANULADA
            venta.save(update_fields=['estado'])

        messages.success(request, f'Venta {venta.numero} anulada y stock devuelto.')
        return redirect('sales:sale_detail', pk=venta.pk)

    contexto = {'venta': venta, 'seccion_activa': 'ventas'}
    return render(request, 'sales/sale_confirm_void.html', contexto)
