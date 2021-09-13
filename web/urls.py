from django.urls import path

from . import views

urlpatterns = [
    path('', views.page),
    path('about', views.page, kwargs={'page_id': 'about'}),
    path('help/syntax', views.page, kwargs={'page_id': 'help/syntax'}),
]
