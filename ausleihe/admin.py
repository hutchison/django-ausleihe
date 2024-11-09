from django.contrib import admin

from .models import (
    Autor,
    Buch,
    Gebaeude,
    Leihe,
    Medium,
    Raum,
    Reservierung,
    Skill,
    Skillset,
    SkillsetItem,
    SkillsetItemRelation,
    Verlag,
    Verfuegbarkeit,
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

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    model = Skill

    list_display = (
        "nummer",
        "name",
        "min_personen",
        "max_personen",
        "anzahl_plaetze",
        "dauer",
    )

    list_display_links = ["name"]
    filter_horizontal = ["raeume"]

@admin.register(Skillset)
class SkillsetAdmin(admin.ModelAdmin):
    model = Skillset

@admin.register(SkillsetItem)
class SkillsetItemAdmin(admin.ModelAdmin):
    model = SkillsetItem

@admin.register(SkillsetItemRelation)
class SkillsetItemRelationAdmin(admin.ModelAdmin):
    model = SkillsetItemRelation

@admin.register(Gebaeude)
class GebaeudeAdmin(admin.ModelAdmin):
    model = Gebaeude
    list_display = (
        "name",
        "lsf_id",
    )

@admin.register(Raum)
class RaumAdmin(admin.ModelAdmin):
    model = Raum
    list_display = (
        "name",
        "lsf_id",
        "anzahl_plaetze",
    )

@admin.register(Verfuegbarkeit)
class VerfuegbarkeitAdmin(admin.ModelAdmin):
    model = Verfuegbarkeit
    list_display = (
        "beginn",
        "ende",
        "raum",
    )

@admin.register(Reservierung)
class ReservierungAdmin(admin.ModelAdmin):
    model = Reservierung
    list_display = (
        "zeit",
        "ende",
        "nutzer",
        "skill",
        "raum",
        "medium",
        "erzeugt",
    )
    search_fields = [
        "nutzer__user__username",
        "nutzer__user__first_name",
        "nutzer__user__last_name",
        "skill__name",
        "raum__name",
        "medium__pk",
    ]
