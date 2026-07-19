"""
Formularios de la app repairs.
"""

from django import forms

from .models import RepairOrder


class RepairOrderForm(forms.ModelForm):
    """Formulario de creación/edición de la cabecera de la orden de servicio."""

    class Meta:
        model = RepairOrder
        fields = (
            'cliente', 'tecnico', 'equipo', 'marca', 'modelo_equipo', 'imei',
            'falla_reportada', 'diagnostico', 'concepto_servicio', 'mano_obra',
            'iva_porcentaje', 'observaciones',
        )
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'tecnico': forms.Select(attrs={'class': 'form-select'}),
            'equipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Celular, Tablet...'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Samsung, Apple...'}),
            'modelo_equipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Galaxy S21'}),
            'imei': forms.TextInput(attrs={'class': 'form-control'}),
            'falla_reportada': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnostico': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'concepto_servicio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cambio de pantalla OLED iPhone 13',
            }),
            'mano_obra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'iva_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limitar el selector de técnico a usuarios con rol técnico o admin
        from accounts.models import CustomUser
        self.fields['tecnico'].queryset = CustomUser.objects.filter(
            role__in=[CustomUser.Roles.TECNICO, CustomUser.Roles.ADMIN]
        )
        self.fields['tecnico'].required = False
        self.fields['diagnostico'].required = False


class RepairStatusForm(forms.Form):
    """Formulario para actualizar el estado de la orden (workflow)."""

    nuevo_estado = forms.ChoiceField(
        label='Nuevo estado',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    nota = forms.CharField(
        label='Nota (opcional)',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )

    def __init__(self, *args, orden=None, **kwargs):
        super().__init__(*args, **kwargs)
        if orden is not None:
            # Solo mostrar estados válidos para la transición + el actual
            opciones = [(orden.estado, orden.get_estado_display() + ' (actual)')]
            for estado in orden.transiciones_validas():
                opciones.append((estado, dict(RepairOrder.Estado.choices)[estado]))
            self.fields['nuevo_estado'].choices = opciones
