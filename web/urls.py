from django.urls import path

from . import views

urlpatterns = [
    path('help/pattern-format', views.page),
    path('', views.page),
]
