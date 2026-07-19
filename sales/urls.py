"""
URLs de la app sales (Ventas).
"""

from django.urls import path

from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('nueva/', views.sale_create, name='sale_create'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/imprimir/', views.sale_print, name='sale_print'),
    path('<int:pk>/anular/', views.sale_void, name='sale_void'),
    # Endpoints JSON
    path('api/clientes/', views.client_search, name='client_search'),
    path('api/productos/', views.product_search, name='product_search'),
]
