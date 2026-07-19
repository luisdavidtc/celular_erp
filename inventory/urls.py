"""
URLs de la app inventory.
"""

from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    # Productos
    path('', views.product_list, name='product_list'),
    path('productos/nuevo/', views.product_create, name='product_create'),
    path('productos/<int:pk>/editar/', views.product_update, name='product_update'),
    path('productos/<int:pk>/eliminar/', views.product_delete, name='product_delete'),
    # Categorías
    path('categorias/', views.category_list, name='category_list'),
    path('categorias/nueva/', views.category_create, name='category_create'),
    path('categorias/<int:pk>/editar/', views.category_update, name='category_update'),
    path('categorias/<int:pk>/eliminar/', views.category_delete, name='category_delete'),
]
