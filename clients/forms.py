"""
Formularios de la app clients.
"""

from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    """Formulario para crear y editar clientes."""

    class Meta:
        model = Client
        fields = ('nombre', 'apellido', 'documento', 'telefono', 'email', 'direccion')
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'documento': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
        }
