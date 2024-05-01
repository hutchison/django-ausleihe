from django.contrib import admin

from .models import (
    Autor,
    Buch,
    Leihe,
    Medium,
    Skillset,
    SkillsetItem,
    SkillsetItemRelation,
    Verlag,
)


class BuchInlineAdmin(admin.StackedInline):
    model = Buch
    extra = 1
    filter_horizontal = ["autoren"]

@admin.register(Buch)
class BuchAdmin(admin.ModelAdmin):
    model = Buch
    list_display = ("titel", "medium", "isbn", "verlag", "ausgabe", "beschreibung")
    fields = (
        ("medium", "isbn"),
        "titel",
        "autoren",
        ("verlag", "ausgabe"),
        "beschreibung",
    )
    search_fields = ["titel", "medium", "isbn", "verlag", "beschreibung"]
    filter_horizontal = ["autoren"]

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    model = Autor
    list_display = ("nachname", "vorname")
    search_fields = ["vorname", "nachname"]

@admin.register(Verlag)
class VerlagAdmin(admin.ModelAdmin):
    model = Verlag

@admin.register(Medium)
class MediumAdmin(admin.ModelAdmin):
    model = Medium

@admin.register(Leihe)
class LeiheAdmin(admin.ModelAdmin):
    model = Leihe
    readonly_fields = ("anfang", "erzeugt", "verleiht_von")
    fields = (
        ("medium", "nutzer"),
        ("anfang", "ende"),
        ("erzeugt", "verleiht_von"),
        "zurueckgebracht",
    )
    list_display = (
        "medium",
        "nutzer",
        "anfang",
        "ende",
        "zurueckgebracht",
        "erzeugt",
        "verleiht_von"
    )

@admin.register(Skillset)
class SkillsetAdmin(admin.ModelAdmin):
    model = Skillset

@admin.register(SkillsetItem)
class SkillsetItemAdmin(admin.ModelAdmin):
    model = SkillsetItem

@admin.register(SkillsetItemRelation)
class SkillsetItemRelationAdmin(admin.ModelAdmin):
    model = SkillsetItemRelation
