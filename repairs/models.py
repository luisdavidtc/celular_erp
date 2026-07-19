"""
Modelos de la app repairs (Servicio Técnico).

Define la orden de servicio (RepairOrder) y los repuestos usados
en la reparación (RepairPart).
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

from clients.models import Client
from inventory.models import Product

IVA_POR_DEFECTO = Decimal('19.00')


class RepairOrder(models.Model):
    """Orden de servicio técnico / reparación."""

    class Estado(models.TextChoices):
        RECIBIDO = 'recibido', 'Recibido'
        DIAGNOSTICO = 'diagnostico', 'En diagnóstico'
        ESPERANDO_REPUESTOS = 'esperando_repuestos', 'Esperando repuestos'
        EN_REPARACION = 'en_reparacion', 'En reparación'
        REPARADO = 'reparado', 'Reparado'
        ENTREGADO = 'entregado', 'Entregado'

    # Transiciones de estado permitidas (workflow)
    TRANSICIONES = {
        Estado.RECIBIDO: [Estado.DIAGNOSTICO, Estado.ENTREGADO],
        Estado.DIAGNOSTICO: [Estado.ESPERANDO_REPUESTOS, Estado.EN_REPARACION, Estado.ENTREGADO],
        Estado.ESPERANDO_REPUESTOS: [Estado.EN_REPARACION, Estado.ENTREGADO],
        Estado.EN_REPARACION: [Estado.REPARADO, Estado.ENTREGADO],
        Estado.REPARADO: [Estado.ENTREGADO],
        Estado.ENTREGADO: [],
    }

    numero_orden = models.CharField('Número de orden', max_length=20, unique=True, blank=True)
    cliente = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='ordenes_servicio',
        verbose_name='Cliente',
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordenes_servicio',
        verbose_name='Técnico',
        null=True,
        blank=True,
    )

    equipo = models.CharField('Equipo', max_length=120)
    marca = models.CharField('Marca', max_length=80, blank=True)
    modelo_equipo = models.CharField('Modelo del equipo', max_length=80, blank=True)
    imei = models.CharField('IMEI / Serial', max_length=60, blank=True)

    falla_reportada = models.TextField('Falla reportada')
    diagnostico = models.TextField('Diagnóstico', blank=True)
    concepto_servicio = models.CharField(
        'Concepto de servicio (para la factura)',
        max_length=200,
        blank=True,
        help_text=(
            'Descripción corta y comercial de lo que se hizo, ej. "Cambio de '
            'pantalla OLED iPhone 13". Es el único concepto que verá el '
            'cliente en la factura cuando el desglose de mano de obra y '
            'repuestos está desactivado (ver Configuración de Empresa → '
            'Ventas). Si se deja en blanco, se genera uno automáticamente '
            'a partir del equipo.'
        ),
    )

    costo_repuestos = models.DecimalField('Costo de repuestos', max_digits=14, decimal_places=2, default=0)
    mano_obra = models.DecimalField('Mano de obra', max_digits=14, decimal_places=2, default=0)
    iva_porcentaje = models.DecimalField('IVA (%)', max_digits=5, decimal_places=2, default=IVA_POR_DEFECTO)
    iva_valor = models.DecimalField('IVA ($)', max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField('Total', max_digits=14, decimal_places=2, default=0)

    estado = models.CharField('Estado', max_length=25, choices=Estado.choices, default=Estado.RECIBIDO)
    fecha_recepcion = models.DateTimeField('Fecha de recepción', auto_now_add=True)
    fecha_entrega = models.DateTimeField('Fecha de entrega', null=True, blank=True)
    observaciones = models.TextField('Observaciones', blank=True)

    venta = models.OneToOneField(
        'sales.Sale',
        on_delete=models.PROTECT,
        related_name='orden_servicio',
        verbose_name='Venta asociada',
        null=True,
        blank=True,
        help_text=(
            'Venta generada automáticamente al facturar esta orden (ver '
            'RepairOrder.facturar). Al ser OneToOne, su sola presencia '
            'impide que la orden se facture dos veces.'
        ),
    )

    class Meta:
        verbose_name = 'Orden de servicio'
        verbose_name_plural = 'Órdenes de servicio'
        ordering = ['-fecha_recepcion']

    def __str__(self):
        return f'{self.numero_orden} - {self.equipo}'

    @property
    def concepto_display(self):
        """Texto de servicio a mostrar en la factura agrupada.

        Usa `concepto_servicio` si el técnico lo escribió; si no, arma un
        texto razonable a partir del equipo/marca/modelo para no dejar la
        factura con una línea vacía.
        """
        if self.concepto_servicio:
            return self.concepto_servicio
        partes = [p for p in (self.equipo, self.marca, self.modelo_equipo) if p]
        return f'Servicio técnico - {" ".join(partes)}' if partes else 'Servicio técnico'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Generar número de orden si no existe (requiere pk)
        if not self.numero_orden:
            self.numero_orden = f'OS-{self.pk:05d}'
            super().save(update_fields=['numero_orden'])

    def recalcular(self, guardar=True):
        """Recalcula costo de repuestos, IVA y total.

        costo_repuestos = suma de subtotales de repuestos
        total = (costo_repuestos + mano_obra) + IVA
        """
        costo_repuestos = sum(
            (parte.subtotal for parte in self.repuestos.all()), Decimal('0')
        )
        base = costo_repuestos + (self.mano_obra or Decimal('0'))
        iva_valor = (base * self.iva_porcentaje / Decimal('100')).quantize(Decimal('0.01'))
        total = (base + iva_valor).quantize(Decimal('0.01'))

        self.costo_repuestos = costo_repuestos.quantize(Decimal('0.01'))
        self.iva_valor = iva_valor
        self.total = total
        if guardar:
            self.save(update_fields=['costo_repuestos', 'iva_valor', 'total'])

    def transiciones_validas(self):
        """Devuelve la lista de estados a los que puede pasar la orden."""
        return self.TRANSICIONES.get(self.estado, [])

    def puede_transicionar_a(self, nuevo_estado):
        return nuevo_estado in self.TRANSICIONES.get(self.estado, [])

    def facturar(self, usuario):
        """Genera la Venta (módulo Ventas) correspondiente a esta reparación.

        Reutiliza los modelos existentes Sale y SaleItem (no crea un sistema
        nuevo de facturación). La venta incluye:
        - Un ítem de mano de obra (si mano_obra > 0), asociado a un producto
          "concepto de servicio" de inventario (ver _producto_servicio).
        - Un ítem por cada repuesto usado en la reparación. Si el repuesto
          está vinculado a un Product real del inventario se usa ese
          producto (para conservar el precio de compra real y así calcular
          la ganancia correctamente); si el repuesto fue cargado solo con
          descripción libre (sin Product), se usa un producto "concepto"
          genérico de repuesto de servicio técnico.

        No vuelve a descontar stock: el stock de los repuestos ya se
        descontó al agregarlos a la orden (ver repairs.views.order_create).
        Los productos "concepto" no representan inventario físico, así que
        tampoco se les descuenta stock.

        Devuelve la Venta creada. Lanza ValueError si la orden ya fue
        facturada o si no tiene nada que facturar.
        """
        from django.db import transaction

        from sales.models import Sale, SaleItem

        if self.venta_id:
            raise ValueError(
                f'La orden {self.numero_orden} ya fue facturada '
                f'(venta {self.venta.numero}).'
            )

        repuestos = list(self.repuestos.select_related('producto').all())
        tiene_mano_obra = bool(self.mano_obra and self.mano_obra > 0)
        if not repuestos and not tiene_mano_obra:
            raise ValueError(
                'La orden no tiene mano de obra ni repuestos registrados; '
                'no hay nada que facturar.'
            )

        with transaction.atomic():
            # Bloquea la fila de la orden para que dos clics/solicitudes
            # concurrentes de "Facturar" no generen dos ventas para la
            # misma reparación (protección adicional a la restricción
            # OneToOne de la base de datos).
            orden = RepairOrder.objects.select_for_update().get(pk=self.pk)
            if orden.venta_id:
                raise ValueError(
                    f'La orden {orden.numero_orden} ya fue facturada '
                    f'(venta {orden.venta.numero}).'
                )

            venta = Sale(
                cliente=orden.cliente,
                vendedor=usuario,
                estado=Sale.Estado.COMPLETADA,
                iva_porcentaje=orden.iva_porcentaje,
                observaciones=(
                    f'Generada automáticamente desde la orden de servicio '
                    f'{orden.numero_orden}.'
                ),
            )
            venta.save()
            venta.asignar_numero_factura()

            if tiene_mano_obra:
                producto_mo = _producto_servicio(
                    codigo='SERV-MANO-OBRA',
                    nombre='Mano de obra técnica',
                )
                SaleItem.objects.create(
                    venta=venta,
                    producto=producto_mo,
                    cantidad=1,
                    precio_unitario=orden.mano_obra,
                    precio_compra=Decimal('0'),
                )

            for parte in repuestos:
                if parte.producto_id:
                    producto_item = parte.producto
                    precio_compra = parte.producto.precio_compra
                else:
                    producto_item = _producto_servicio(
                        codigo='SERV-REPUESTO-GEN',
                        nombre='Repuesto de servicio técnico (genérico)',
                    )
                    precio_compra = Decimal('0')

                SaleItem.objects.create(
                    venta=venta,
                    producto=producto_item,
                    cantidad=parte.cantidad,
                    precio_unitario=parte.precio_unitario,
                    precio_compra=precio_compra,
                )

            venta.recalcular()

            orden.venta = venta
            orden.save(update_fields=['venta'])
            self.venta = venta

        return venta


def _producto_servicio(codigo, nombre):
    """Obtiene (o crea) el producto "concepto" usado para representar
    conceptos de servicio técnico (mano de obra o repuestos sin catálogo)
    como ítems de Venta, reutilizando el modelo Product existente en vez
    de crear un modelo nuevo.

    Se marca con stock=1 y stock_minimo=0 para que nunca aparezca en el
    indicador de "Inventario bajo" del Dashboard (1 > 0), sin necesidad de
    tocar esa consulta. No se le descuenta stock al facturar, ya que no
    representa una unidad física de inventario.
    """
    from inventory.models import Category, Product

    categoria, _ = Category.objects.get_or_create(
        nombre='Servicios Técnicos',
        defaults={'descripcion': 'Conceptos de servicio técnico facturables (no son inventario físico).'},
    )
    producto, _ = Product.objects.get_or_create(
        codigo=codigo,
        defaults={
            'nombre': nombre,
            'categoria': categoria,
            'descripcion': 'Producto concepto generado automáticamente por la integración Servicio Técnico → Ventas.',
            'precio_compra': Decimal('0'),
            'precio_venta': Decimal('0'),
            'stock': 1,
            'stock_minimo': 0,
        },
    )
    return producto


class RepairPart(models.Model):
    """Repuesto utilizado en una orden de servicio."""

    orden = models.ForeignKey(
        RepairOrder,
        on_delete=models.CASCADE,
        related_name='repuestos',
        verbose_name='Orden',
    )
    producto = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        related_name='repuestos_usados',
        verbose_name='Producto / Repuesto',
        null=True,
        blank=True,
    )
    descripcion = models.CharField('Descripción', max_length=200)
    cantidad = models.PositiveIntegerField('Cantidad', default=1)
    precio_unitario = models.DecimalField('Precio unitario', max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField('Subtotal', max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Repuesto'
        verbose_name_plural = 'Repuestos'

    def __str__(self):
        return f'{self.cantidad} x {self.descripcion}'

    def calcular_subtotal(self):
        self.subtotal = (self.precio_unitario * self.cantidad).quantize(Decimal('0.01'))
        return self.subtotal

    def save(self, *args, **kwargs):
        self.calcular_subtotal()
        super().save(*args, **kwargs)
