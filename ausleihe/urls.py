from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'ausleihe'

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
