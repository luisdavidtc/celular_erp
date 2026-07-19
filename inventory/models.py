"""
Modelos de la app inventory.
"""

from django.db import models


class Category(models.Model):
    """Categoría de productos."""

    nombre = models.CharField('Nombre', max_length=100, unique=True)
    descripcion = models.TextField('Descripción', blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Product(models.Model):
    """Producto del inventario."""

    nombre = models.CharField('Nombre', max_length=150)
    categoria = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='productos',
        verbose_name='Categoría',
    )
    codigo = models.CharField('Código', max_length=50, unique=True)
    codigo_barras = models.CharField('Código de barras', max_length=100, blank=True)
    descripcion = models.TextField('Descripción', blank=True)
    precio_compra = models.DecimalField('Precio de compra', max_digits=12, decimal_places=2, default=0)
    precio_venta = models.DecimalField('Precio de venta', max_digits=12, decimal_places=2, default=0)
    stock = models.PositiveIntegerField('Stock', default=0)
    stock_minimo = models.PositiveIntegerField('Stock mínimo', default=0)
    marca = models.CharField('Marca', max_length=100, blank=True)
    modelo = models.CharField('Modelo', max_length=100, blank=True)
    imagen = models.ImageField('Imagen', upload_to='productos/', blank=True, null=True)
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'

    @property
    def stock_bajo(self):
        """Indica si el stock está en o por debajo del mínimo."""
        return self.stock <= self.stock_minimo
