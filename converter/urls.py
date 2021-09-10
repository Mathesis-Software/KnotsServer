from django.urls import path

from . import views

urlpatterns = [
    path('<str:code>', views.index, name='index'),
]
