"""
Utilidades de la app company.

Contiene helpers reutilizables por otras apps (sales, repairs) para la
impresión de comprobantes, evitando duplicar la lógica de generación de QR
y de obtención de la configuración de empresa.
"""

import base64
from io import BytesIO

import qrcode


def generar_qr_data_uri(contenido):
    """Genera un código QR a partir de un texto y lo devuelve como data URI PNG.

    El resultado puede usarse directamente en un template como:
        <img src="{{ qr_data_uri }}">
    sin necesidad de guardar ningún archivo en disco.
    """
    if not contenido:
        return None

    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(contenido)
    qr.make(fit=True)
    imagen = qr.make_image(fill_color='black', back_color='white')

    buffer = BytesIO()
    imagen.save(buffer, format='PNG')
    codificado = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f'data:image/png;base64,{codificado}'


def obtener_configuracion_empresa():
    """Devuelve la empresa y todos sus sub-modelos de configuración.

    Crea cada sub-modelo si aún no existe (por ejemplo, si el administrador
    todavía no ha guardado ninguna pestaña en Configuración de Empresa),
    para que las vistas de impresión de otras apps (sales, repairs) nunca
    fallen por un OneToOne inexistente.
    """
    from .models import (
        BrandingSettings,
        Company,
        EmailSettings,
        InvoiceSettings,
        PrintSettings,
        SalesSettings,
        WhatsAppSettings,
    )

    empresa = Company.get_solo()
    branding, _creado = BrandingSettings.objects.get_or_create(company=empresa)
    facturacion, _creado = InvoiceSettings.objects.get_or_create(company=empresa)
    ventas_cfg, _creado = SalesSettings.objects.get_or_create(company=empresa)
    impresion, _creado = PrintSettings.objects.get_or_create(company=empresa)
    whatsapp_cfg, _creado = WhatsAppSettings.objects.get_or_create(company=empresa)
    correo_cfg, _creado = EmailSettings.objects.get_or_create(company=empresa)

    return {
        'empresa': empresa,
        'branding': branding,
        'facturacion': facturacion,
        'ventas_cfg': ventas_cfg,
        'impresion': impresion,
        'whatsapp_cfg': whatsapp_cfg,
        'correo_cfg': correo_cfg,
    }

