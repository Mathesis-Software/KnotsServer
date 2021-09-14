from django.urls import path

from . import views

urlpatterns = [
    path('diagram', views.diagram4Code),
    path('test/<str:code>', views.test),
]
