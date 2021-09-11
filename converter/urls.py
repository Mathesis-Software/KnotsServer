from django.urls import path

from . import views

urlpatterns = [
    path('diagram4code', views.diagram4Code),
    path('<str:code>', views.index, name='index'),
]
