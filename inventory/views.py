"""
Vistas de la app inventory: CRUD de productos y categorías.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, ProductForm
from .models import Category, Product


# ===================== Productos =====================

@login_required
def product_list(request):
    """Lista de productos con búsqueda y filtros."""
    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    solo_stock_bajo = request.GET.get('stock_bajo', '') == '1'

    productos = Product.objects.select_related('categoria').all()
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda)
            | Q(codigo__icontains=busqueda)
            | Q(codigo_barras__icontains=busqueda)
            | Q(marca__icontains=busqueda)
            | Q(modelo__icontains=busqueda)
        )
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if solo_stock_bajo:
        productos = productos.filter(stock__lte=F('stock_minimo'))

    contexto = {
        'productos': productos,
        'categorias': Category.objects.all(),
        'busqueda': busqueda,
        'categoria_id': categoria_id,
        'solo_stock_bajo': solo_stock_bajo,
        'seccion_activa': 'inventario',
    }
    return render(request, 'inventory/product_list.html', contexto)


@login_required
def product_create(request):
    """Crear un nuevo producto."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado correctamente.')
            return redirect('inventory:product_list')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = ProductForm()
    contexto = {'form': form, 'titulo': 'Nuevo producto', 'seccion_activa': 'inventario'}
    return render(request, 'inventory/product_form.html', contexto)


@login_required
def product_update(request, pk):
    """Editar un producto existente."""
    producto = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('inventory:product_list')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = ProductForm(instance=producto)
    contexto = {
        'form': form,
        'titulo': f'Editar producto: {producto.nombre}',
        'seccion_activa': 'inventario',
    }
    return render(request, 'inventory/product_form.html', contexto)


@login_required
def product_delete(request, pk):
    """Eliminar un producto."""
    producto = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado correctamente.')
        return redirect('inventory:product_list')
    contexto = {'producto': producto, 'seccion_activa': 'inventario'}
    return render(request, 'inventory/product_confirm_delete.html', contexto)


# ===================== Categorías =====================

@login_required
def category_list(request):
    """Lista de categorías."""
    categorias = Category.objects.all()
    contexto = {'categorias': categorias, 'seccion_activa': 'inventario'}
    return render(request, 'inventory/category_list.html', contexto)


@login_required
def category_create(request):
    """Crear una nueva categoría."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada correctamente.')
            return redirect('inventory:category_list')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = CategoryForm()
    contexto = {'form': form, 'titulo': 'Nueva categoría', 'seccion_activa': 'inventario'}
    return render(request, 'inventory/category_form.html', contexto)


@login_required
def category_update(request, pk):
    """Editar una categoría existente."""
    categoria = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada correctamente.')
            return redirect('inventory:category_list')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = CategoryForm(instance=categoria)
    contexto = {
        'form': form,
        'titulo': f'Editar categoría: {categoria.nombre}',
        'seccion_activa': 'inventario',
    }
    return render(request, 'inventory/category_form.html', contexto)


@login_required
def category_delete(request, pk):
    """Eliminar una categoría."""
    categoria = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        if categoria.productos.exists():
            messages.error(request, 'No se puede eliminar: la categoría tiene productos asociados.')
            return redirect('inventory:category_list')
        categoria.delete()
        messages.success(request, 'Categoría eliminada correctamente.')
        return redirect('inventory:category_list')
    contexto = {'categoria': categoria, 'seccion_activa': 'inventario'}
    return render(request, 'inventory/category_confirm_delete.html', contexto)
