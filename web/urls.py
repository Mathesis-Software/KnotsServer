from django.urls import path

from . import views

urlpatterns = [
    path('', views.page),
    path('about', views.page, kwargs={'page_id': 'about'}),
    path('help/search', views.page, kwargs={'page_id': 'help/search'}),
]
