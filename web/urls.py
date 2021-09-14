from django.urls import path

from . import views

urlpatterns = [
    path('', views.page),
    path('about', views.page, kwargs={'page_id': 'about'}),
    path('help/search', views.page, kwargs={'page_id': 'help/search'}),
]

handler400 = views.error
handler403 = views.error
handler404 = views.error
handler500 = views.page
