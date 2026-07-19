"""
Vistas de la app repairs (Servicio Técnico).

Incluye:
- Creación de orden de servicio con repuestos dinámicos (vía JS).
- Listado con filtros por estado y búsqueda.
- Detalle de orden.
- Actualización de estado con validación de transiciones (workflow).
- Al agregar repuestos del inventario se descuenta stock.
- Registro automático de cambios de estado en RepairOrderStatusLog.
"""

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from company.utils import generar_qr_data_uri, obtener_configuracion_empresa
from inventory.models import Product

from .forms import RepairOrderForm, RepairStatusForm
from .models import RepairOrder, RepairPart, RepairOrderStatusLog

# Roles que pueden gestionar servicio técnico
ROLES_SERVICIO = ('admin', 'tecnico')


def _to_decimal(valor, por_defecto='0'):
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(por_defecto)


@login_required
@role_required(*ROLES_SERVICIO)
def order_list(request):
    """Lista de órdenes de servicio con filtros por estado y búsqueda."""
    estado = request.GET.get('estado', '').strip()
    busqueda = request.GET.get('q', '').strip()

    ordenes = RepairOrder.objects.select_related('cliente', 'tecnico').all()
    if estado:
        ordenes = ordenes.filter(estado=estado)
    if busqueda:
        ordenes = ordenes.filter(
            Q(numero_orden__icontains=busqueda)
            | Q(cliente__nombre__icontains=busqueda)
            | Q(cliente__apellido__icontains=busqueda)
            | Q(cliente__documento__icontains=busqueda)
            | Q(equipo__icontains=busqueda)
            | Q(imei__icontains=busqueda)
            | Q(marca__icontains=busqueda)
        )

    contexto = {
        'ordenes': ordenes,
        'estado': estado,
        'busqueda': busqueda,
        'estados': RepairOrder.Estado.choices,
        'seccion_activa': 'servicio',
    }
    return render(request, 'repairs/order_list.html', contexto)


@login_required
@role_required(*ROLES_SERVICIO)
def order_create(request):
    """Crear una nueva orden de servicio con repuestos dinámicos."""
    if request.method == 'POST':
        form = RepairOrderForm(request.POST)

        # Repuestos enviados en arrays paralelos
        producto_ids = request.POST.getlist('parte_producto_id')
        descripciones = request.POST.getlist('parte_descripcion')
        cantidades = request.POST.getlist('parte_cantidad')
        precios = request.POST.getlist('parte_precio')

        if form.is_valid():
            try:
                with transaction.atomic():
                    orden = form.save(commit=False)
                    if not orden.tecnico:
                        # Si no se asignó técnico y el usuario es técnico, asignarlo
                        if request.user.role == 'tecnico':
                            orden.tecnico = request.user
                    orden.save()  # genera numero_orden

                    for idx, descripcion in enumerate(descripciones):
                        descripcion = (descripcion or '').strip()
                        cantidad = int(cantidades[idx]) if idx < len(cantidades) and cantidades[idx] else 0
                        if not descripcion or cantidad <= 0:
                            continue

                        prod_id = producto_ids[idx] if idx < len(producto_ids) else ''
                        producto = None
                        if prod_id:
                            producto = get_object_or_404(Product, pk=prod_id)
                            if cantidad > producto.stock:
                                raise ValueError(
                                    f'Stock insuficiente para "{producto.nombre}". '
                                    f'Disponible: {producto.stock}, solicitado: {cantidad}.'
                                )

                        precio = _to_decimal(precios[idx]) if idx < len(precios) else Decimal('0')

                        RepairPart.objects.create(
                            orden=orden,
                            producto=producto,
                            descripcion=descripcion,
                            cantidad=cantidad,
                            precio_unitario=precio,
                        )

                        # Descontar stock si proviene del inventario
                        if producto:
                            producto.stock -= cantidad
                            producto.save(update_fields=['stock'])

                    orden.recalcular()

                messages.success(request, f'Orden {orden.numero_orden} creada correctamente.')
                return redirect('repairs:order_detail', pk=orden.pk)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = RepairOrderForm()

    contexto = {
        'form': form,
        'titulo': 'Nueva orden de servicio',
        'seccion_activa': 'servicio',
    }
    return render(request, 'repairs/order_form.html', contexto)


@login_required
@role_required(*ROLES_SERVICIO)
def order_detail(request, pk):
    """Detalle de una orden de servicio."""
    orden = get_object_or_404(
        RepairOrder.objects.select_related('cliente', 'tecnico'), pk=pk
    )
    status_form = RepairStatusForm(orden=orden)
    
    # Obtener historial de cambios de estado (logs)
    logs_estado = orden.logs_estado.select_related('usuario').all()
    
    contexto = {
        'orden': orden,
        'repuestos': orden.repuestos.select_related('producto').all(),
        'status_form': status_form,
        'logs_estado': logs_estado,
        'seccion_activa': 'servicio',
    }
    return render(request, 'repairs/order_detail.html', contexto)


@login_required
@role_required(*ROLES_SERVICIO)
def order_print(request, pk):
    """Recibo de orden de servicio técnico imprimible (ticket o carta).

    Usa los mismos datos de Configuración de Empresa que el comprobante de
    venta (identidad visual, facturación, impresión), más las condiciones
    de garantía de servicio técnico configuradas en la pestaña Facturación.
    """
    orden = get_object_or_404(
        RepairOrder.objects.select_related('cliente', 'tecnico'), pk=pk
    )
    config = obtener_configuracion_empresa()
    empresa = config['empresa']
    impresion = config['impresion']

    qr_contenido = None
    if impresion.mostrar_qr:
        qr_contenido = (
            f'Orden {orden.numero_orden} | {empresa.nombre_comercial or empresa.razon_social} '
            f'| Cliente: {orden.cliente.nombre} {orden.cliente.apellido} '
            f'| Estado: {orden.get_estado_display()} | Total: {empresa.simbolo_moneda}{orden.total}'
        )

    contexto = {
        'orden': orden,
        'repuestos': orden.repuestos.select_related('producto').all(),
        'empresa': empresa,
        'branding': config['branding'],
        'facturacion': config['facturacion'],
        'impresion': impresion,
        'qr_data_uri': generar_qr_data_uri(qr_contenido),
    }
    return render(request, 'repairs/order_print.html', contexto)


@login_required
@role_required(*ROLES_SERVICIO)
def order_update_status(request, pk):
    """Actualizar el estado de una orden validando transiciones lógicas.
    
    Registra automáticamente cada cambio de estado en RepairOrderStatusLog
    con usuario, fecha/hora y notas opcionales.
    """
    orden = get_object_or_404(RepairOrder, pk=pk)
    if request.method == 'POST':
        form = RepairStatusForm(request.POST, orden=orden)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['nuevo_estado']
            nota = form.cleaned_data.get('nota', '').strip()

            if nuevo_estado == orden.estado:
                messages.info(request, 'El estado no cambió.')
                return redirect('repairs:order_detail', pk=orden.pk)

            if not orden.puede_transicionar_a(nuevo_estado):
                messages.error(
                    request,
                    f'Transición no permitida: de "{orden.get_estado_display()}" '
                    f'no se puede pasar al estado seleccionado.'
                )
                return redirect('repairs:order_detail', pk=orden.pk)

            # Guardar estado anterior para el log
            estado_anterior = orden.estado
            
            # Actualizar estado
            orden.estado = nuevo_estado
            if nuevo_estado == RepairOrder.Estado.ENTREGADO:
                orden.fecha_entrega = timezone.now()
            
            orden.save(update_fields=['estado', 'fecha_entrega'])
            
            # Registrar cambio en log de auditoría
            RepairOrderStatusLog.objects.create(
                orden=orden,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                usuario=request.user,
                notas=nota,
            )
            
            messages.success(request, f'Estado actualizado a "{orden.get_estado_display()}".')
        else:
            messages.error(request, 'No se pudo actualizar el estado.')
    return redirect('repairs:order_detail', pk=orden.pk)


@login_required
@role_required(*ROLES_SERVICIO)
def order_invoice(request, pk):
    """Factura la orden de servicio: genera una Venta (módulo Ventas) a
    partir de la mano de obra y los repuestos de la orden, reutilizando
    los modelos Sale/SaleItem existentes (ver RepairOrder.facturar).

    Solo acepta POST. Si la orden ya fue facturada, no se crea una venta
    nueva (RepairOrder.venta es OneToOne y RepairOrder.facturar valida
    explícitamente esta condición dentro de una transacción con bloqueo
    de fila).
    
    Después de facturar exitosamente, cambia el estado a FACTURADO.
    """
    orden = get_object_or_404(RepairOrder, pk=pk)
    if request.method != 'POST':
        return redirect('repairs:order_detail', pk=orden.pk)

    # Validar que la orden está en estado LISTO_PARA_ENTREGAR
    if orden.estado != RepairOrder.Estado.LISTO_PARA_ENTREGAR:
        messages.error(
            request,
            f'La orden debe estar en estado "Listo para entregar" para facturar. '
            f'Estado actual: "{orden.get_estado_display()}".'
        )
        return redirect('repairs:order_detail', pk=orden.pk)

    try:
        with transaction.atomic():
            venta = orden.facturar(request.user)
            
            # Cambiar estado a FACTURADO
            estado_anterior = orden.estado
            orden.estado = RepairOrder.Estado.FACTURADO
            orden.save(update_fields=['estado'])
            
            # Registrar cambio en log de auditoría
            RepairOrderStatusLog.objects.create(
                orden=orden,
                estado_anterior=estado_anterior,
                estado_nuevo=RepairOrder.Estado.FACTURADO,
                usuario=request.user,
                notas='Facturación automática al crear venta',
            )
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('repairs:order_detail', pk=orden.pk)

    messages.success(
        request,
        f'Orden {orden.numero_orden} facturada correctamente como venta {venta.numero}.',
    )
    return redirect('sales:sale_detail', pk=venta.pk)
