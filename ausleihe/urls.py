from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'ausleihe'

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('autoren', views.AutorList.as_view(), name='autor-list'),
    path('autoren/neu', views.AutorCreate.as_view(), name='autor-create'),
    path('autoren/<int:autor_id>/bearbeiten', views.AutorEdit.as_view(), name='autor-edit'),
    path('autoren/<int:autor_id>', views.AutorDetail.as_view(), name='autor-detail'),
    path('bücher', views.BuchList.as_view(), name='buch-list'),
    path('bücher/neu', views.BuchCreate.as_view(), name='buch-create'),
    path('bücher/<int:buch_id>', views.BuchDetail.as_view(), name='buch-detail'),
    path('bücher/<int:buch_id>/bearbeiten', views.BuchEdit.as_view(), name='buch-edit'),
    path('medien/<str:medium_id>', views.MediumDetail.as_view(), name='medium-detail'),
    path('verlage', views.VerlagList.as_view(), name='verlag-list'),
    path('verlage/neu', views.VerlagCreate.as_view(), name='verlag-create'),
    path('verlage/<int:verlag_id>', views.VerlagDetail.as_view(), name='verlag-detail'),
    path('verlage/<int:verlag_id>/bearbeiten', views.VerlagEdit.as_view(), name='verlag-edit'),
    path('verleihen', views.Verleihen.as_view(), name='verleihen'),
    path('verliehen', views.LeiheList.as_view(), name='verliehen'),
    path('verliehen/suche', views.LeiheUserSuche.as_view(), name='verliehen-an-suche'),
    path('verliehen/an', views.LeiheUserDetail.as_view(), name='verliehen-an'),
    path('zuruecknehmen/<int:leihe_id>', views.Zuruecknehmen.as_view(), name='zuruecknehmen'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
