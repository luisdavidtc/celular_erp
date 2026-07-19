"""
Vistas de la app company.

Se expone una única vista `company_config` con varias pestañas (una por
sección de configuración). Cada pestaña es un formulario independiente
que se guarda por separado: al enviar un formulario, solo se valida y
guarda la sección correspondiente, sin afectar las demás.

Acceso restringido a administradores.
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.decorators import admin_required

from .forms import (
    BrandingSettingsForm,
    CompanyForm,
    EmailSettingsForm,
    InvoiceSettingsForm,
    PrintSettingsForm,
    SalesSettingsForm,
    WhatsAppSettingsForm,
)
from .utils import obtener_configuracion_empresa

SECCIONES_VALIDAS = (
    'empresa', 'identidad', 'facturacion', 'ventas',
    'impresion', 'whatsapp', 'correo',
)


@admin_required
def company_config(request):
    """Vista de configuración de empresa (pestañas por sección)."""
    config = obtener_configuracion_empresa()
    company = config['empresa']
    branding = config['branding']
    facturacion = config['facturacion']
    ventas_cfg = config['ventas_cfg']
    impresion_cfg = config['impresion']
    whatsapp_cfg = config['whatsapp_cfg']
    correo_cfg = config['correo_cfg']

    # Mapa: nombre de sección -> (clase de formulario, instancia del modelo)
    definicion_secciones = {
        'empresa': (CompanyForm, company),
        'identidad': (BrandingSettingsForm, branding),
        'facturacion': (InvoiceSettingsForm, facturacion),
        'ventas': (SalesSettingsForm, ventas_cfg),
        'impresion': (PrintSettingsForm, impresion_cfg),
        'whatsapp': (WhatsAppSettingsForm, whatsapp_cfg),
        'correo': (EmailSettingsForm, correo_cfg),
    }

    tab_activa = request.GET.get('tab', 'empresa')
    if tab_activa not in SECCIONES_VALIDAS:
        tab_activa = 'empresa'

    if request.method == 'POST':
        seccion = request.POST.get('seccion')
        if seccion in definicion_secciones:
            form_class, instancia = definicion_secciones[seccion]
            form = form_class(request.POST, request.FILES, instance=instancia)
            if form.is_valid():
                form.save()
                messages.success(request, 'Configuración actualizada correctamente.')
                return redirect(f"{reverse('company:config')}?tab={seccion}")
            messages.error(request, 'Corrige los errores del formulario.')
            # Reemplaza el formulario con errores para mostrarlo en la pestaña correspondiente
            definicion_secciones[seccion] = (form_class, instancia)
            tab_activa = seccion
            forms_finales = {
                nombre: (form if nombre == seccion else clase(instance=inst))
                for nombre, (clase, inst) in definicion_secciones.items()
            }
        else:
            forms_finales = {
                nombre: clase(instance=inst)
                for nombre, (clase, inst) in definicion_secciones.items()
            }
    else:
        forms_finales = {
            nombre: clase(instance=inst)
            for nombre, (clase, inst) in definicion_secciones.items()
        }

    contexto = {
        'forms': forms_finales,
        'tab_activa': tab_activa,
        'seccion_activa': 'configuracion_empresa',
    }
    return render(request, 'company/config.html', contexto)
