"""
Vistas de la app accounts: autenticación y gestión de usuarios.
"""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import admin_required
from .forms import LoginForm, UserCreateForm, UserUpdateForm
from .models import CustomUser


def login_view(request):
    """Vista de inicio de sesión."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}.')
            return redirect('dashboard:index')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Cierra la sesión del usuario."""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('accounts:login')


@admin_required
def user_list(request):
    """Lista de usuarios (solo administradores)."""
    busqueda = request.GET.get('q', '').strip()
    usuarios = CustomUser.objects.all().order_by('username')
    if busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=busqueda)
            | Q(first_name__icontains=busqueda)
            | Q(last_name__icontains=busqueda)
            | Q(email__icontains=busqueda)
        )
    contexto = {'usuarios': usuarios, 'busqueda': busqueda}
    return render(request, 'accounts/user_list.html', contexto)


@admin_required
def user_create(request):
    """Crear un nuevo usuario (solo administradores)."""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado correctamente.')
            return redirect('accounts:user_list')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = UserCreateForm()
    contexto = {'form': form, 'titulo': 'Nuevo usuario'}
    return render(request, 'accounts/user_form.html', contexto)


@admin_required
def user_update(request, pk):
    """Editar un usuario existente (solo administradores)."""
    usuario = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('accounts:user_list')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = UserUpdateForm(instance=usuario)
    contexto = {'form': form, 'titulo': f'Editar usuario: {usuario.username}'}
    return render(request, 'accounts/user_form.html', contexto)


@admin_required
def user_delete(request, pk):
    """Eliminar un usuario (solo administradores)."""
    usuario = get_object_or_404(CustomUser, pk=pk)
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('accounts:user_list')
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('accounts:user_list')
    contexto = {'usuario': usuario}
    return render(request, 'accounts/user_confirm_delete.html', contexto)
