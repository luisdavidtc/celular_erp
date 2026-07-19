"""
Formularios de la app sales.
"""

from django import forms

from .models import Sale


class SaleForm(forms.ModelForm):
    """Formulario de cabecera de la venta.

    Las líneas de detalle (ítems) se manejan aparte mediante JavaScript y
    se procesan manualmente en la vista.
    """

    class Meta:
        model = Sale
        fields = ('cliente', 'descuento_porcentaje', 'iva_porcentaje', 'observaciones')
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select', 'id': 'id_cliente'}),
            'descuento_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100',
                'id': 'id_descuento_porcentaje',
            }),
            'iva_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100',
                'id': 'id_iva_porcentaje',
            }),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
