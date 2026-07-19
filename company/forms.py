"""
Formularios de la app company.

Un ModelForm por sección de configuración, para poder mostrarlos como
pestañas independientes y guardarlos por separado sin afectar las demás
secciones.
"""

from django import forms

from .models import (
    BrandingSettings,
    Company,
    EmailSettings,
    InvoiceSettings,
    PrintSettings,
    SalesSettings,
    WhatsAppSettings,
)

_TEXT = forms.TextInput(attrs={'class': 'form-control'})
_TEXTAREA = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
_SELECT = forms.Select(attrs={'class': 'form-select'})
_CHECK = forms.CheckboxInput(attrs={'class': 'form-check-input'})
_NUMBER = forms.NumberInput(attrs={'class': 'form-control'})
_DATE = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
_COLOR = forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'})
_FILE = forms.ClearableFileInput(attrs={'class': 'form-control'})


class CompanyForm(forms.ModelForm):
    """Sección: Empresa (datos generales, fiscales y regionales)."""

    class Meta:
        model = Company
        fields = (
            'nombre_comercial', 'razon_social', 'nit', 'tipo_empresa',
            'regimen_tributario', 'responsable_iva', 'actividad_economica',
            'direccion', 'pais', 'departamento', 'municipio', 'codigo_postal',
            'telefono', 'whatsapp', 'correo', 'sitio_web',
            'moneda', 'simbolo_moneda', 'idioma', 'zona_horaria',
        )
        widgets = {
            'nombre_comercial': _TEXT,
            'razon_social': _TEXT,
            'nit': _TEXT,
            'tipo_empresa': _SELECT,
            'regimen_tributario': _SELECT,
            'responsable_iva': _CHECK,
            'actividad_economica': _TEXT,
            'direccion': _TEXT,
            'pais': _TEXT,
            'departamento': _TEXT,
            'municipio': _TEXT,
            'codigo_postal': _TEXT,
            'telefono': _TEXT,
            'whatsapp': _TEXT,
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'sitio_web': forms.URLInput(attrs={'class': 'form-control'}),
            'moneda': _SELECT,
            'simbolo_moneda': _TEXT,
            'idioma': _SELECT,
            'zona_horaria': _TEXT,
        }


class BrandingSettingsForm(forms.ModelForm):
    """Sección: Identidad Visual."""

    class Meta:
        model = BrandingSettings
        fields = (
            'logo_principal', 'logo_impresion', 'favicon',
            'color_primario', 'color_secundario', 'color_botones', 'tema',
        )
        widgets = {
            'logo_principal': _FILE,
            'logo_impresion': _FILE,
            'favicon': _FILE,
            'color_primario': _COLOR,
            'color_secundario': _COLOR,
            'color_botones': _COLOR,
            'tema': _SELECT,
        }


class InvoiceSettingsForm(forms.ModelForm):
    """Sección: Facturación (numeración y resolución DIAN)."""

    class Meta:
        model = InvoiceSettings
        fields = (
            'prefijo_facturacion', 'consecutivo_inicial', 'consecutivo_actual',
            'resolucion_dian', 'fecha_resolucion', 'fecha_vencimiento_resolucion',
            'tipo_documento', 'nota_legal', 'politica_devolucion', 'mensaje_agradecimiento',
            'condiciones_servicio_tecnico',
        )
        widgets = {
            'prefijo_facturacion': _TEXT,
            'consecutivo_inicial': _NUMBER,
            'consecutivo_actual': _NUMBER,
            'resolucion_dian': _TEXT,
            'fecha_resolucion': _DATE,
            'fecha_vencimiento_resolucion': _DATE,
            'tipo_documento': _SELECT,
            'nota_legal': _TEXTAREA,
            'politica_devolucion': _TEXTAREA,
            'mensaje_agradecimiento': _TEXT,
            'condiciones_servicio_tecnico': _TEXTAREA,
        }


class SalesSettingsForm(forms.ModelForm):
    """Sección: configuración del módulo de Ventas."""

    class Meta:
        model = SalesSettings
        fields = (
            'permitir_venta_sin_stock', 'aplicar_iva_defecto', 'iva_defecto_porcentaje',
            'redondear_precios', 'mostrar_imagen_producto', 'mostrar_codigo_barras',
            'mostrar_descuento', 'mostrar_desglose_servicio_tecnico',
        )
        widgets = {
            'permitir_venta_sin_stock': _CHECK,
            'aplicar_iva_defecto': _CHECK,
            'iva_defecto_porcentaje': _NUMBER,
            'redondear_precios': _CHECK,
            'mostrar_imagen_producto': _CHECK,
            'mostrar_codigo_barras': _CHECK,
            'mostrar_descuento': _CHECK,
            'mostrar_desglose_servicio_tecnico': _CHECK,
        }


class PrintSettingsForm(forms.ModelForm):
    """Sección: configuración de Impresión."""

    class Meta:
        model = PrintSettings
        fields = (
            'tamano_ticket', 'margenes', 'mostrar_logo', 'mostrar_qr',
            'mostrar_codigo_barras', 'copias_defecto',
        )
        widgets = {
            'tamano_ticket': _SELECT,
            'margenes': _TEXT,
            'mostrar_logo': _CHECK,
            'mostrar_qr': _CHECK,
            'mostrar_codigo_barras': _CHECK,
            'copias_defecto': _NUMBER,
        }


class WhatsAppSettingsForm(forms.ModelForm):
    """Sección: configuración de WhatsApp."""

    class Meta:
        model = WhatsAppSettings
        fields = ('numero_principal', 'mensaje_venta', 'mensaje_reparacion', 'mensaje_garantia')
        widgets = {
            'numero_principal': _TEXT,
            'mensaje_venta': _TEXTAREA,
            'mensaje_reparacion': _TEXTAREA,
            'mensaje_garantia': _TEXTAREA,
        }


class EmailSettingsForm(forms.ModelForm):
    """Sección: configuración de Correo."""

    class Meta:
        model = EmailSettings
        fields = ('nombre_remitente', 'correo_remitente', 'firma', 'plantilla_html')
        widgets = {
            'nombre_remitente': _TEXT,
            'correo_remitente': forms.EmailInput(attrs={'class': 'form-control'}),
            'firma': _TEXTAREA,
            'plantilla_html': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }
