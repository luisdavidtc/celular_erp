"""
URLs de la app company.
"""

from django.urls import path

from . import views

app_name = 'company'

urlpatterns = [
    path('', views.company_config, name='config'),
]
