"""
Modelos de la app sales (Ventas).

Define la venta (Sale) y sus líneas de detalle (SaleItem).
Maneja cálculos de subtotal, descuentos, IVA (19% por defecto),
total y ganancia.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

from clients.models import Client
from inventory.models import Product

# IVA por defecto en Colombia
IVA_POR_DEFECTO = Decimal('19.00')


class Sale(models.Model):
    """Venta realizada a un cliente."""

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        COMPLETADA = 'completada', 'Completada'
        ANULADA = 'anulada', 'Anulada'

    cliente = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='ventas',
        verbose_name='Cliente',
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ventas',
        verbose_name='Vendedor',
        null=True,
        blank=True,
    )
    fecha = models.DateTimeField('Fecha', auto_now_add=True)

    invoice_number = models.PositiveIntegerField(
        'Número de factura',
        unique=True,
        null=True,
        blank=True,
        help_text=(
            'Consecutivo de facturación asignado de forma atómica al confirmar '
            'la venta (ver Sale.asignar_numero_factura). Nulo en ventas antiguas '
            'creadas antes de activar la numeración; nunca se reutiliza ni se '
            'genera retroactivamente.'
        ),
    )

    subtotal = models.DecimalField('Subtotal', max_digits=14, decimal_places=2, default=0)
    descuento_porcentaje = models.DecimalField('Descuento (%)', max_digits=5, decimal_places=2, default=0)
    descuento_valor = models.DecimalField('Descuento ($)', max_digits=14, decimal_places=2, default=0)
    iva_porcentaje = models.DecimalField('IVA (%)', max_digits=5, decimal_places=2, default=IVA_POR_DEFECTO)
    iva_valor = models.DecimalField('IVA ($)', max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField('Total', max_digits=14, decimal_places=2, default=0)
    ganancia = models.DecimalField('Ganancia', max_digits=14, decimal_places=2, default=0)

    observaciones = models.TextField('Observaciones', blank=True)
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=Estado.choices,
        default=Estado.COMPLETADA,
    )

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']

    def __str__(self):
        return f'Venta #{self.pk} - {self.cliente.nombre_completo}'

    @property
    def numero(self):
        """Número de venta formateado (identificador interno, para uso en el ERP)."""
        return f'V-{self.pk:05d}'

    @property
    def numero_factura(self):
        """Número de factura formateado con ceros (6 dígitos), sin prefijo.

        Devuelve None si la venta todavía no tiene consecutivo asignado
        (ventas antiguas anteriores a este módulo). No se genera
        retroactivamente: el template debe mostrar "Sin asignar" en ese caso.
        El prefijo (ej. "FE") se combina en el template a partir de
        InvoiceSettings.prefijo_facturacion, ya que este modelo no conoce
        la configuración de empresa.
        """
        if self.invoice_number is None:
            return None
        return f'{self.invoice_number:06d}'

    def asignar_numero_factura(self):
        """Asigna el siguiente consecutivo de facturación de forma atómica.

        Debe invocarse dentro de una transacción atómica ya abierta por
        quien llama (ej. sale_create), para que el bloqueo de fila
        (select_for_update) y el guardado del consecutivo incrementado
        formen una sola unidad con el resto de la creación de la venta.

        No hace nada si la venta ya tiene un invoice_number (evita
        reasignar o duplicar en llamadas repetidas).
        """
        if self.invoice_number is not None:
            return

        from company.models import Company, InvoiceSettings

        empresa = Company.get_solo()
        # Garantiza que exista la fila antes de bloquearla; select_for_update
        # no puede bloquear un registro que aún no existe.
        InvoiceSettings.objects.get_or_create(company=empresa)
        facturacion = InvoiceSettings.objects.select_for_update().get(company=empresa)

        numero_asignado = facturacion.consecutivo_actual
        facturacion.consecutivo_actual = numero_asignado + 1
        facturacion.save(update_fields=['consecutivo_actual'])

        self.invoice_number = numero_asignado
        self.save(update_fields=['invoice_number'])

    def recalcular(self, guardar=True):
        """
        Recalcula los totales de la venta a partir de sus ítems.

        subtotal = suma de subtotales de ítems
        descuento_valor = descuento_porcentaje aplicado al subtotal
                          (se respeta descuento_valor si ya viene cargado y
                           el porcentaje es 0)
        base gravable = subtotal - descuento_valor
        iva_valor = base gravable * iva_porcentaje
        total = base gravable + iva_valor
        ganancia = (precio_unitario - precio_compra) * cantidad por ítem,
                   menos el descuento aplicado.
        """
        items = list(self.items.all())
        subtotal = sum((it.subtotal for it in items), Decimal('0'))

        # Descuento: prioriza el porcentaje si es > 0, si no usa el valor fijo
        if self.descuento_porcentaje and self.descuento_porcentaje > 0:
            descuento_valor = (subtotal * self.descuento_porcentaje / Decimal('100'))
        else:
            descuento_valor = self.descuento_valor or Decimal('0')

        descuento_valor = descuento_valor.quantize(Decimal('0.01'))
        if descuento_valor > subtotal:
            descuento_valor = subtotal

        base_gravable = subtotal - descuento_valor
        iva_valor = (base_gravable * self.iva_porcentaje / Decimal('100')).quantize(Decimal('0.01'))
        total = (base_gravable + iva_valor).quantize(Decimal('0.01'))

        # Ganancia bruta de los ítems
        ganancia_items = sum(
            ((it.precio_unitario - it.precio_compra) * it.cantidad - it.descuento for it in items),
            Decimal('0'),
        )
        # Se descuenta el descuento global de la ganancia
        ganancia = (ganancia_items - descuento_valor).quantize(Decimal('0.01'))

        self.subtotal = subtotal.quantize(Decimal('0.01'))
        self.descuento_valor = descuento_valor
        self.iva_valor = iva_valor
        self.total = total
        self.ganancia = ganancia
        if guardar:
            self.save(update_fields=[
                'subtotal', 'descuento_valor', 'iva_valor', 'total', 'ganancia',
            ])


class SaleItem(models.Model):
    """Línea de detalle de una venta."""

    venta = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Venta',
    )
    producto = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='ventas_items',
        verbose_name='Producto',
    )
    cantidad = models.PositiveIntegerField('Cantidad', default=1)
    precio_unitario = models.DecimalField('Precio unitario', max_digits=12, decimal_places=2, default=0)
    precio_compra = models.DecimalField('Precio de compra', max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField('Descuento ($)', max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField('Subtotal', max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Ítem de venta'
        verbose_name_plural = 'Ítems de venta'

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'

    def calcular_subtotal(self):
        """Calcula el subtotal de la línea (cantidad * precio - descuento)."""
        bruto = self.precio_unitario * self.cantidad
        self.subtotal = (bruto - (self.descuento or Decimal('0'))).quantize(Decimal('0.01'))
        return self.subtotal

    def save(self, *args, **kwargs):
        self.calcular_subtotal()
        super().save(*args, **kwargs)
