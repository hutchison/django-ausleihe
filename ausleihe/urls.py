from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'ausleihe'

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('medien', views.MediumList.as_view(), name='medium-list'),
    path('medien/<str:medium_id>', views.MediumDetail.as_view(), name='medium-detail'),
    path('bücher', views.BuchList.as_view(), name='buch-list'),
    path('bücher/neu', views.BuchCreate.as_view(), name='buch-create'),
    path('bücher/<int:buch_id>', views.BuchDetail.as_view(), name='buch-detail'),
    path('bücher/<int:buch_id>/bearbeiten', views.BuchEdit.as_view(), name='buch-edit'),
    path('autoren', views.AutorList.as_view(), name='autor-list'),
    path('autoren/neu', views.AutorCreate.as_view(), name='autor-create'),
    path('autoren/<int:autor_id>/bearbeiten', views.AutorEdit.as_view(), name='autor-edit'),
    path('autoren/<int:autor_id>', views.AutorDetail.as_view(), name='autor-detail'),
    path('verlage', views.VerlagList.as_view(), name='verlag-list'),
    path('verlage/neu', views.VerlagCreate.as_view(), name='verlag-create'),
    path('verlage/<int:verlag_id>', views.VerlagDetail.as_view(), name='verlag-detail'),
    path('verlage/<int:verlag_id>/bearbeiten', views.VerlagEdit.as_view(), name='verlag-edit'),
    path('skills', views.SkillList.as_view(), name='skill-list'),
    path('skills/neu', views.SkillCreate.as_view(), name='skill-create'),
    path('skills/<int:skill_id>', views.SkillDetail.as_view(), name='skill-detail'),
    path('skills/<int:skill_id>/bearbeiten', views.SkillEdit.as_view(), name='skill-edit'),
    path('skillsets', views.SkillsetList.as_view(), name='skillset-list'),
    path('skillsets/<int:skillset_id>', views.SkillsetDetail.as_view(), name='skillset-detail'),
    path('skillsets/<int:skillset_id>/bearbeiten', views.SkillsetEdit.as_view(), name='skillset-edit'),
    path('skillsets/neu', views.SkillsetCreate.as_view(), name='skillset-create'),
    path('skillsetitems', views.SkillsetItemList.as_view(), name='skillsetitem-list'),
    path('skillsetitems/neu', views.SkillsetItemCreate.as_view(), name='skillsetitem-create'),
    path('skillsetitems/<int:skillsetitem_id>/bearbeiten', views.SkillsetItemEdit.as_view(), name='skillsetitem-edit'),
    path('skillsetitems/<int:skillsetitem_id>/loeschen', views.SkillsetItemDelete.as_view(), name='skillsetitem-delete'),
    path('räume', views.RaumList.as_view(), name='raum-list'),
    path('raum/neu', views.RaumCreate.as_view(), name='raum-create'),
    path('raum/<int:raum_id>/bearbeiten', views.RaumEdit.as_view(), name='raum-edit'),
    path('raum/importieren', views.RaumImport.as_view(), name='raum-import'),
    path('verleihen', views.Verleihen.as_view(), name='verleihen'),
    path('verliehen', views.LeiheList.as_view(), name='verliehen'),
    path('verliehen/suche', views.LeiheUserSuche.as_view(), name='verliehen-an-suche'),
    path('verliehen/an', views.LeiheUserDetail.as_view(), name='verliehen-an'),
    path('zuruecknehmen/<int:leihe_id>', views.Zuruecknehmen.as_view(), name='zuruecknehmen'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
