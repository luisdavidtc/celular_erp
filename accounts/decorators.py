"""
Decoradores y mixins para el control de acceso por rol.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*roles):
    """
    Decorador que restringe el acceso a una vista según los roles indicados.

    Los superusuarios y administradores siempre tienen acceso.
    Uso: @role_required('admin', 'vendedor')
    """

    def decorador(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            usuario = request.user
            if usuario.is_superuser or usuario.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            raise PermissionDenied
        return _wrapped

    return decorador


def admin_required(view_func):
    """Decorador que restringe el acceso solo a administradores."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.es_admin:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Solo los administradores pueden acceder a esta sección.')
        raise PermissionDenied
    return _wrapped


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin para vistas basadas en clases que restringe el acceso por rol.

    Definir `allowed_roles` en la vista. Los administradores y superusuarios
    siempre tienen acceso.
    """

    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.es_admin or request.user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        raise PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin que restringe el acceso solo a administradores."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.es_admin:
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, 'Solo los administradores pueden acceder a esta sección.')
        raise PermissionDenied
