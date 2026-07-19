"""
Modelos de la app company (Configuración de Empresa).

Contiene el modelo núcleo `Company` (datos generales, fiscales, regionales
y de sistema) y seis sub-modelos relacionados 1 a 1, cada uno enfocado en
una sección de configuración: Identidad Visual, Facturación, Ventas,
Impresión, WhatsApp y Correo.

Patrón singleton
-----------------
En esta fase el ERP administra una sola empresa. Por eso `Company` se
maneja como singleton: solo existirá el registro con pk=1, obtenido
siempre mediante `Company.get_solo()`. Esto simplifica la UI (no hay que
elegir "cuál empresa" configurar) y a la vez prepara el terreno para una
futura evolución SaaS multiempresa: cuando llegue ese momento, bastará con
quitar la restricción de singleton y relacionar cada `Company` con un
`Tenant`/`Organization`, sin tener que rediseñar los campos ni las
secciones ya definidas aquí.

Los campos `estado`, `activo`, `licencia` y `version_erp` ya están
presentes para cuando se active la facturación por suscripción (SaaS),
aunque todavía no se implementa esa lógica.
"""

from django.db import models


class Company(models.Model):
    """Datos generales, fiscales, regionales y de sistema de la empresa.

    Núcleo del módulo de configuración. Se maneja como singleton
    (siempre pk=1); usar `Company.get_solo()` para obtener/crear el
    registro en vez de instanciar el modelo directamente.
    """

    class TipoEmpresa(models.TextChoices):
        NATURAL = 'natural', 'Persona Natural'
        JURIDICA = 'juridica', 'Persona Jurídica'

    class RegimenTributario(models.TextChoices):
        SIMPLIFICADO = 'simplificado', 'Régimen Simplificado'
        COMUN = 'comun', 'Régimen Común'
        SIMPLE = 'simple', 'Régimen Simple de Tributación'
        NO_RESPONSABLE = 'no_responsable', 'No Responsable de IVA'

    class Moneda(models.TextChoices):
        COP = 'COP', 'Peso Colombiano (COP)'
        USD = 'USD', 'Dólar Estadounidense (USD)'
        EUR = 'EUR', 'Euro (EUR)'
        MXN = 'MXN', 'Peso Mexicano (MXN)'

    class Idioma(models.TextChoices):
        ES = 'es', 'Español'
        EN = 'en', 'Inglés'

    class Estado(models.TextChoices):
        ACTIVA = 'activa', 'Activa'
        SUSPENDIDA = 'suspendida', 'Suspendida'
        PRUEBA = 'prueba', 'En prueba'

    # --- Datos generales ---
    nombre_comercial = models.CharField('Nombre comercial', max_length=150, blank=True)
    razon_social = models.CharField('Razón social', max_length=150, blank=True)
    nit = models.CharField('NIT', max_length=30, blank=True)
    tipo_empresa = models.CharField(
        'Tipo de empresa', max_length=20,
        choices=TipoEmpresa.choices, blank=True,
    )
    regimen_tributario = models.CharField(
        'Régimen tributario', max_length=20,
        choices=RegimenTributario.choices, blank=True,
    )
    responsable_iva = models.BooleanField('Responsable de IVA', default=True)
    actividad_economica = models.CharField(
        'Actividad económica', max_length=150, blank=True,
        help_text='Código CIIU y/o descripción de la actividad principal.',
    )

    # --- Ubicación ---
    direccion = models.CharField('Dirección', max_length=255, blank=True)
    pais = models.CharField('País', max_length=100, blank=True, default='Colombia')
    departamento = models.CharField('Departamento', max_length=100, blank=True)
    municipio = models.CharField('Municipio / Ciudad', max_length=100, blank=True)
    codigo_postal = models.CharField('Código postal', max_length=20, blank=True)

    # --- Contacto ---
    telefono = models.CharField('Teléfono', max_length=30, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=30, blank=True)
    correo = models.EmailField('Correo electrónico', blank=True)
    sitio_web = models.URLField('Sitio web', blank=True)

    # --- Regional ---
    moneda = models.CharField('Moneda', max_length=3, choices=Moneda.choices, default=Moneda.COP)
    simbolo_moneda = models.CharField('Símbolo de moneda', max_length=5, default='$')
    idioma = models.CharField('Idioma', max_length=5, choices=Idioma.choices, default=Idioma.ES)
    zona_horaria = models.CharField('Zona horaria', max_length=50, default='America/Bogota')

    # --- Sistema (preparado para SaaS) ---
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)
    fecha_modificacion = models.DateTimeField('Fecha de última modificación', auto_now=True)
    estado = models.CharField('Estado', max_length=20, choices=Estado.choices, default=Estado.ACTIVA)
    activo = models.BooleanField('Activo', default=True)
    licencia = models.CharField('Licencia', max_length=50, blank=True, default='Estándar')
    version_erp = models.CharField('Versión del ERP', max_length=20, blank=True, default='1.0')

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Configuración de Empresa'

    def __str__(self):
        return self.nombre_comercial or 'Configuración de la empresa'

    def save(self, *args, **kwargs):
        # Fuerza el patrón singleton: siempre pk=1.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        """Devuelve el único registro de configuración de empresa, creándolo si no existe."""
        obj, _creado = cls.objects.get_or_create(pk=1)
        return obj


class BrandingSettings(models.Model):
    """Identidad visual de la empresa (logos, colores, tema)."""

    class Tema(models.TextChoices):
        CLARO = 'claro', 'Claro'
        OSCURO = 'oscuro', 'Oscuro'
        AUTO = 'auto', 'Automático'

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name='identidad_visual',
    )
    logo_principal = models.ImageField(
        'Logo principal', upload_to='empresa/logos/', blank=True, null=True,
        help_text='Usado en el dashboard, PDF y correo electrónico.',
    )
    logo_impresion = models.ImageField(
        'Logo para impresión', upload_to='empresa/logos/', blank=True, null=True,
        help_text='Versión optimizada (monocromática) para impresión térmica.',
    )
    favicon = models.ImageField('Favicon', upload_to='empresa/favicon/', blank=True, null=True)
    color_primario = models.CharField('Color primario', max_length=7, default='#2563eb')
    color_secundario = models.CharField('Color secundario', max_length=7, default='#9333ea')
    color_botones = models.CharField('Color de botones', max_length=7, default='#2563eb')
    tema = models.CharField('Tema', max_length=10, choices=Tema.choices, default=Tema.CLARO)

    class Meta:
        verbose_name = 'Identidad Visual'
        verbose_name_plural = 'Identidad Visual'

    def __str__(self):
        return f'Identidad visual de {self.company}'


class InvoiceSettings(models.Model):
    """Configuración de facturación y resolución DIAN."""

    class TipoDocumento(models.TextChoices):
        FACTURA_VENTA = 'factura_venta', 'Factura de Venta'
        POS = 'pos', 'Documento POS'
        NOTA_CREDITO = 'nota_credito', 'Nota Crédito'
        NOTA_DEBITO = 'nota_debito', 'Nota Débito'

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name='facturacion',
    )
    prefijo_facturacion = models.CharField('Prefijo de facturación', max_length=10, blank=True)
    consecutivo_inicial = models.PositiveIntegerField('Consecutivo inicial', default=1)
    consecutivo_actual = models.PositiveIntegerField('Consecutivo actual', default=1)
    resolucion_dian = models.CharField('Resolución DIAN', max_length=50, blank=True)
    fecha_resolucion = models.DateField('Fecha de resolución', null=True, blank=True)
    fecha_vencimiento_resolucion = models.DateField(
        'Fecha de vencimiento de la resolución', null=True, blank=True,
    )
    tipo_documento = models.CharField(
        'Tipo de documento', max_length=20,
        choices=TipoDocumento.choices, default=TipoDocumento.FACTURA_VENTA,
    )
    nota_legal = models.TextField('Nota legal', blank=True)
    politica_devolucion = models.TextField('Política de devolución', blank=True)
    mensaje_agradecimiento = models.CharField('Mensaje de agradecimiento', max_length=255, blank=True)
    condiciones_servicio_tecnico = models.TextField(
        'Condiciones de garantía (Servicio Técnico)', blank=True,
        default='Garantía de 30 días calendario sobre el repuesto instalado. '
                'No cubre daños por mal uso, humedad o intervención de terceros.',
        help_text='Texto que se muestra en el pie del recibo de servicio técnico.',
    )

    class Meta:
        verbose_name = 'Configuración de Facturación'
        verbose_name_plural = 'Configuración de Facturación'

    def __str__(self):
        return f'Facturación de {self.company}'


class SalesSettings(models.Model):
    """Configuración del comportamiento del módulo de Ventas."""

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name='ventas_config',
    )
    permitir_venta_sin_stock = models.BooleanField('Permitir vender sin stock', default=False)
    aplicar_iva_defecto = models.BooleanField('Aplicar IVA por defecto', default=True)
    iva_defecto_porcentaje = models.DecimalField(
        'IVA por defecto (%)', max_digits=5, decimal_places=2, default=19,
    )
    redondear_precios = models.BooleanField('Redondear precios', default=False)
    mostrar_imagen_producto = models.BooleanField('Mostrar imagen del producto', default=True)
    mostrar_codigo_barras = models.BooleanField('Mostrar código de barras', default=True)
    mostrar_descuento = models.BooleanField('Mostrar descuento', default=True)
    mostrar_desglose_servicio_tecnico = models.BooleanField(
        'Mostrar desglose de mano de obra y repuestos en facturas de Servicio Técnico',
        default=False,
        help_text=(
            'Desactivado (recomendado): la factura generada al facturar una '
            'reparación muestra un único concepto de servicio con el precio '
            'final. Activado: se listan por separado la mano de obra y cada '
            'repuesto utilizado, igual que en una venta normal.'
        ),
    )

    class Meta:
        verbose_name = 'Configuración de Ventas'
        verbose_name_plural = 'Configuración de Ventas'

    def __str__(self):
        return f'Configuración de ventas de {self.company}'


class PrintSettings(models.Model):
    """Configuración de impresión de tickets/facturas."""

    class TamanoTicket(models.TextChoices):
        MM58 = '58mm', '58 mm'
        MM80 = '80mm', '80 mm'
        CARTA = 'carta', 'Carta'

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name='impresion',
    )
    tamano_ticket = models.CharField(
        'Tamaño de ticket', max_length=10,
        choices=TamanoTicket.choices, default=TamanoTicket.MM80,
    )
    margenes = models.CharField(
        'Márgenes (mm)', max_length=50, default='5,5,5,5',
        help_text='Formato: superior,inferior,izquierdo,derecho',
    )
    mostrar_logo = models.BooleanField('Mostrar logo', default=True)
    mostrar_qr = models.BooleanField('Mostrar QR', default=False)
    mostrar_codigo_barras = models.BooleanField('Mostrar código de barras', default=False)
    copias_defecto = models.PositiveSmallIntegerField('Copias por defecto', default=1)

    class Meta:
        verbose_name = 'Configuración de Impresión'
        verbose_name_plural = 'Configuración de Impresión'

    def __str__(self):
        return f'Configuración de impresión de {self.company}'


class WhatsAppSettings(models.Model):
    """Configuración de mensajes automáticos por WhatsApp."""

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name='whatsapp_config',
    )
    numero_principal = models.CharField('Número principal', max_length=30, blank=True)
    mensaje_venta = models.TextField(
        'Mensaje automático de venta', blank=True,
        default='Hola {cliente}, gracias por tu compra #{numero}. Total: {total}.',
    )
    mensaje_reparacion = models.TextField(
        'Mensaje automático de reparación', blank=True,
        default='Hola {cliente}, tu equipo (orden {numero}) ha cambiado de estado: {estado}.',
    )
    mensaje_garantia = models.TextField(
        'Mensaje automático de garantía', blank=True,
        default='Hola {cliente}, tu garantía para el producto {producto} vence el {fecha_vencimiento}.',
    )

    class Meta:
        verbose_name = 'Configuración de WhatsApp'
        verbose_name_plural = 'Configuración de WhatsApp'

    def __str__(self):
        return f'Configuración de WhatsApp de {self.company}'


class EmailSettings(models.Model):
    """Configuración de envío de correo electrónico."""

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name='correo_config',
    )
    nombre_remitente = models.CharField('Nombre remitente', max_length=150, blank=True)
    correo_remitente = models.EmailField('Correo remitente', blank=True)
    firma = models.TextField('Firma', blank=True)
    plantilla_html = models.TextField(
        'Plantilla HTML', blank=True,
        help_text='Plantilla base reutilizable para los correos enviados por el sistema.',
    )

    class Meta:
        verbose_name = 'Configuración de Correo'
        verbose_name_plural = 'Configuración de Correo'

    def __str__(self):
        return f'Configuración de correo de {self.company}'
