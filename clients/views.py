"""
Vistas de la app clients: CRUD de clientes.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from .forms import ClientForm
from .models import Client

# Roles que pueden modificar clientes (el técnico solo tiene consulta)
ROLES_EDITAR_CLIENTES = ('admin', 'vendedor')


@login_required
def client_list(request):
    """Lista de clientes con búsqueda."""
    busqueda = request.GET.get('q', '').strip()
    clientes = Client.objects.all()
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda)
            | Q(apellido__icontains=busqueda)
            | Q(documento__icontains=busqueda)
            | Q(telefono__icontains=busqueda)
            | Q(email__icontains=busqueda)
        )
    contexto = {
        'clientes': clientes,
        'busqueda': busqueda,
        'seccion_activa': 'clientes',
    }
    return render(request, 'clients/client_list.html', contexto)


@login_required
@role_required(*ROLES_EDITAR_CLIENTES)
def client_create(request):
    """Crear un nuevo cliente."""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado correctamente.')
            return redirect('clients:client_list')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = ClientForm()
    contexto = {
        'form': form,
        'titulo': 'Nuevo cliente',
        'seccion_activa': 'clientes',
    }
    return render(request, 'clients/client_form.html', contexto)


@login_required
@role_required(*ROLES_EDITAR_CLIENTES)
def client_update(request, pk):
    """Editar un cliente existente."""
    cliente = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente.')
            return redirect('clients:client_list')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = ClientForm(instance=cliente)
    contexto = {
        'form': form,
        'titulo': f'Editar cliente: {cliente.nombre_completo}',
        'seccion_activa': 'clientes',
    }
    return render(request, 'clients/client_form.html', contexto)


@login_required
@role_required(*ROLES_EDITAR_CLIENTES)
def client_delete(request, pk):
    """Eliminar un cliente."""
    cliente = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado correctamente.')
        return redirect('clients:client_list')
    contexto = {'cliente': cliente, 'seccion_activa': 'clientes'}
    return render(request, 'clients/client_confirm_delete.html', contexto)
