from django.contrib import admin

from .models import (
    Medium,
    Buch,
    BuchAutor,
)

class MediumAdmin(admin.ModelAdmin):
    model = Medium

admin.site.register(Medium, MediumAdmin)

class BuchAdmin(admin.ModelAdmin):
    model = Buch
    list_display = ("titel", "medium", "isbn", "verlag", "ausgabe", "beschreibung")
    fields = (("medium", "isbn"), "titel", ("verlag", "ausgabe"), "beschreibung")
    search_fields = ["titel", "medium", "isbn", "verlag", "beschreibung"]

admin.site.register(Buch, BuchAdmin)

class BuchAutorAdmin(admin.ModelAdmin):
    model = BuchAutor
    list_display = ("nachname", "vorname")
    search_fields = ["vorname", "nachname"]

admin.site.register(BuchAutor, BuchAutorAdmin)
