"""
URLs de la app repairs (Servicio Técnico).
"""

from django.urls import path

from . import views

app_name = 'repairs'

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('nueva/', views.order_create, name='order_create'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/imprimir/', views.order_print, name='order_print'),
    path('<int:pk>/estado/', views.order_update_status, name='order_update_status'),
    path('<int:pk>/facturar/', views.order_invoice, name='order_invoice'),
]
