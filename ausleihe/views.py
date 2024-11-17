from datetime import date, datetime, timedelta, time
from random import choice
from math import ceil

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView

import requests

from fsmedhro_core.models import FachschaftUser, Kontaktdaten

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
from .forms import (
    GebaeudeForm,
    RaumForm,
    RaumImportForm,
    ReservierungszeitForm,
    SkillForm,
    SkillsetForm,
    VerfuegbarkeitForm,
)
from .parsers import LSFRoomParser


class Home(LoginRequiredMixin, View):
    template_name = "ausleihe/home.html"

    def get(self, request):
        try:
            fuser = FachschaftUser.objects.get(user=request.user)
        except FachschaftUser.DoesNotExist:
            return render(request, "ausleihe/profil_unvollstaendig.html")
        else:
            aktuell_reserviert = Reservierung.objects.prefetch_related(
                "skill",
                "raum",
            ).filter(
                nutzer=fuser,
                zeit__gte=timezone.now(),
            )

            aktuell_verliehen = Leihe.objects.prefetch_related(
                "medium__buecher",
                "medium__skillsets",
                "verleiht_von__fachschaftuser",
            ).filter(
                zurueckgebracht=False,
                nutzer=fuser,
            )

            historisch_verliehen = Leihe.objects.prefetch_related(
                "medium__buecher",
                "medium__skillsets",
                "verleiht_von__fachschaftuser",
            ).filter(
                zurueckgebracht=True,
                nutzer=fuser,
            )

            context = {
                "aktuell_reserviert": aktuell_reserviert,
                "aktuell_verliehen": aktuell_verliehen,
                "historisch_verliehen": historisch_verliehen,
            }

            return render(request, self.template_name, context)


class MediumList(LoginRequiredMixin, ListView):
    queryset = Medium.objects.prefetch_related(
        "buecher",
        "skillsets",
    )


class MediumDetail(LoginRequiredMixin, DetailView):
    model = Medium
    pk_url_kwarg = "medium_id"


class AutorList(LoginRequiredMixin, ListView):
    model = Autor


class AutorDetail(LoginRequiredMixin, DetailView):
    model = Autor
    pk_url_kwarg = "autor_id"


class AutorCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Autor
    permission_required = "ausleihe.add_autor"
    fields = ["vorname", "nachname"]
    template_name_suffix = "_create"

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:autor-list")


class AutorEdit(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Autor
    permission_required = "ausleihe.change_autor"
    fields = ["vorname", "nachname"]
    pk_url_kwarg = "autor_id"
    template_name_suffix = "_edit"

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:autor-detail", kwargs={"autor_id": self.object.id})


class BuchList(LoginRequiredMixin, ListView):
    queryset = Buch.objects.prefetch_related(
        "medium",
        "autoren",
        "verlag",
    )


class BuchDetail(LoginRequiredMixin, DetailView):
    model = Buch
    pk_url_kwarg = "buch_id"


class BuchCreate(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "ausleihe.add_buch"
    template_name = "ausleihe/buch_create.html"

    def get_common_context(self):
        context = {
            "verlage": Verlag.objects.all(),
            "autoren": Autor.objects.all(),
        }
        return context

    def get(self, request):
        context = self.get_common_context()
        return render(request, self.template_name, context)

    def post(self, request):
        errors = {}
        context = self.get_common_context()

        buch = Buch.dict_from_post_data(request.POST)
        autoren_ids = list(map(int, request.POST.getlist("autoren")))
        autoren = Autor.objects.filter(id__in=autoren_ids)

        context.update({"buch": buch})

        if Medium.objects.filter(id=buch["medium_id"]).exists():
            messages.warning(
                request,
                "Ein Medium mit dieser Nummer existiert schon."
            )

        if not buch["titel"]:
            errors["titel"] = "Der Titel ist zwingend erforderlich."
            context["errors"] = errors
            context["buch"]["autoren"] = {"all": autoren}
            return render(request, self.template_name, context)
        else:
            m = Medium.objects.create(id=buch["medium_id"])

            b = Buch(**buch)
            b.medium = m
            b.save()

            b.autoren.set(autoren)

            messages.success(request, f"{b} hinzugefügt!")

            return redirect("ausleihe:buch-list")


class BuchEdit(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Buch
    permission_required = "ausleihe.change_buch"
    fields = ["titel", "medium", "isbn", "ausgabe", "verlag", "beschreibung", "autoren"]
    pk_url_kwarg = "buch_id"
    template_name_suffix = "_edit"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["verlage"] = Verlag.objects.all()
        context["autoren"] = Autor.objects.all()

        return context

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:buch-detail", kwargs={"buch_id": self.object.id})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        errors = {}
        context = self.get_context_data()

        neues_b = Buch.dict_from_post_data(request.POST)

        autoren_ids = list(map(int, request.POST.getlist("autoren")))
        autoren = Autor.objects.filter(id__in=autoren_ids)

        context.update({"buch": neues_b})

        if not neues_b["titel"]:
            errors["titel"] = "Der Titel ist zwingend erforderlich."
            context["errors"] = errors
            context["buch"]["autoren"] = {"all": autoren}
            return self.render_to_response(context)
        else:
            buch = Buch(**neues_b)
            buch.id = self.object.id

            medium_changed = self.object.medium_id != neues_b["medium_id"]
            new_medium_exists = Medium.objects.filter(id=neues_b["medium_id"]).exists()

            if medium_changed:
                if new_medium_exists:
                    ref_buecher = Buch.objects.filter(medium_id=neues_b["medium_id"])
                    if ref_buecher.exists():
                        messages.warning(
                            request,
                            "Die Mediatheknummer von diesem Buch existiert schon. "
                            "Folgende andere Bücher sind der Mediatheknr. "
                            f"{neues_b['medium_id']} zugeordnet: " +
                            ", ".join(map(str, list(ref_buecher)))
                        )
                else:
                    buch.medium = Medium.objects.create(id=neues_b["medium_id"])
                    messages.warning(
                        request,
                        "Die Mediatheknummer von diesem Buch wurde neu erzeugt. "
                        f"Die alte Nummer {buch.medium_nr} existiert noch und "
                        "könnte ggf. gelöscht werden."
                    )

            buch.save()
            buch.autoren.set(autoren)

            return redirect(self.get_success_url())


class VerlagList(LoginRequiredMixin, ListView):
    model = Verlag


class VerlagDetail(LoginRequiredMixin, DetailView):
    model = Verlag
    pk_url_kwarg = "verlag_id"


class VerlagCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Verlag
    permission_required = "ausleihe.add_verlag"
    fields = ["name"]
    template_name_suffix = "_create"

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:verlag-list")


class VerlagEdit(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Verlag
    permission_required = "ausleihe.change_verlag"
    fields = ["name"]
    pk_url_kwarg = "verlag_id"
    template_name_suffix = "_edit"

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:verlag-detail", kwargs={"verlag_id": self.object.id})


class Verleihen(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = "ausleihe/verleihen.html"
    permission_required = "ausleihe.add_leihe"
    user_model = get_user_model()

    def get_common_context(self):
        fs_user = FachschaftUser.objects.prefetch_related(
            "user", "kontaktdaten",
        ).order_by(
            "user__last_name",
            "user__first_name",
        )

        context = {
            "medien": Medium.objects.all(),
            "nutzer": fs_user,
            "anfang": timezone.now(),
            "ende": (
                datetime.combine(timezone.now().date(), time.max)
                + timedelta(days=30)
            ),
        }
        return context

    def get(self, request):
        context = self.get_common_context()
        return render(request, self.template_name, context)

    def post(self, request):
        context = self.get_common_context()
        errors = {}

        medium_id = request.POST.get("medium_id")
        nutzer_id = request.POST.get("nutzer_id")

        # überpfüe Eingabefehler:

        if not Medium.objects.filter(id=medium_id).exists():
            errors["medium_id"] = "Mediatheknummer existiert nicht."
            context["medium_id"] = medium_id

        if not FachschaftUser.objects.filter(id=nutzer_id).exists():
            errors["nutzer_id"] = "Nutzer:in existiert nicht."
            context["nutzer_id"] = nutzer_id

        if errors:
            context["errors"] = errors
            return render(request, self.template_name, context)

        medium = Medium.objects.get(id=medium_id)
        nutzer = FachschaftUser.objects.get(id=nutzer_id)
        anfang = timezone.make_aware(
            datetime.fromisoformat(request.POST.get("anfang"))
        )
        ende = timezone.make_aware(
            datetime.fromisoformat(request.POST.get("ende"))
        )

        # überprüfe logische Fehler:

        if ende < anfang:
            errors["ende"] = "Ende darf nicht vor dem Anfang liegen."

        if medium.aktuell_ausgeliehen():
            errors["aktuell_ausgeliehen"] = True

        if errors:
            context["errors"] = errors
            return render(request, self.template_name, context)

        leihe = Leihe(
            medium=medium,
            nutzer=nutzer,
            anfang=anfang,
            ende=ende,
            verleiht_von=request.user,
        )
        leihe.save()

        context["verliehen_an"] = nutzer
        context["verliehen_bis"] = ende
        context["verleih_erfolgreich"] = True

        return render(request, self.template_name, context)


class Zuruecknehmen(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "ausleihe.change_leihe"

    def get(self, request, leihe_id):
        l = Leihe.objects.filter(id=leihe_id).update(
            zurueckgebracht=True,
            ende=timezone.now(),
        )

        redirect_next = request.GET.get("next", None)
        if redirect_next == "reservierungen":
            return redirect("ausleihe:reservierung-list")

        username = request.GET.get("username", None)
        if username:
            # umleiten zu verliehen-an:
            url = reverse("ausleihe:verliehen-an")
            parameter = urlencode({"username": username})
            return redirect(f"{url}?{parameter}")

        return redirect("ausleihe:verliehen")


class LeiheList(LoginRequiredMixin, ListView):
    queryset = Leihe.objects.prefetch_related(
        "medium",
        "medium__buecher",
        "medium__skillsets",
        "nutzer__user",
        "verleiht_von__fachschaftuser",
    ).filter(
        zurueckgebracht=False,
    ).order_by(
        "ende",
        "nutzer",
    )

class LeiheUserDetail(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "ausleihe.view_leihe"
    template_name = "ausleihe/leihe_user_detail.html"
    user_model = get_user_model()

    def get(self, request):
        username = request.GET.get("username", None)

        user = get_object_or_404(self.user_model, username=username)
        fuser = get_object_or_404(
            FachschaftUser,
            user=user.id
        )

        kontaktdaten = Kontaktdaten.objects.filter(fachschaftuser=fuser)

        leihen = Leihe.objects.filter(nutzer=fuser).prefetch_related(
            "medium__buecher",
            "nutzer__user",
            "verleiht_von",
        )

        context = {
            "nutzer": fuser,
            "aktuell_verliehen": leihen.filter(zurueckgebracht=False),
            "historisch_verliehen": leihen.filter(zurueckgebracht=True),
            "kontaktdaten": kontaktdaten,
        }

        return render(request, self.template_name, context)


class LeiheUserSuche(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "ausleihe.view_leihe"
    template_name = "ausleihe/leihe_user_suche.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["nutzer"] = FachschaftUser.objects.prefetch_related("user").order_by(
            "user__last_name",
            "user__first_name",
        )

        return context


class SkillsetList(LoginRequiredMixin, ListView):
    queryset = Skillset.objects.prefetch_related(
        "item_relations",
        "medium",
    )


class SkillsetDetail(LoginRequiredMixin, DetailView):
    queryset = Skillset.objects.prefetch_related(
        "item_relations__item",
    )
    pk_url_kwarg = "skillset_id"


class SkillsetCreate(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "ausleihe.add_skillset"
    template_name = "ausleihe/skillset_create.html"

    def get_common_context(self):
        context = {
            "items": SkillsetItem.objects.all(),
            "skills": Skill.objects.all(),
        }
        return context

    def get(self, request):
        context = self.get_common_context()
        return render(request, self.template_name, context)

    def post(self, request):
        medium_id = request.POST.get("medium_id")
        name = request.POST.get("name")
        item_quantities = request.POST.getlist("item_quantities")
        item_ids = request.POST.getlist("item_ids")
        skill_id = int(request.POST.get("skill_id"))

        skill = get_object_or_404(Skill, id=skill_id)

        medium, created = Medium.objects.get_or_create(pk=medium_id)
        skillset = Skillset.objects.create(
            medium=medium,
            name=name,
            skill=skill,
        )

        skillset_items = [
            (int(quant), int(item_id))
            for quant, item_id in zip(item_quantities, item_ids)
            if quant and item_id
        ]

        for quant, item_id in skillset_items:
            SkillsetItemRelation.objects.create(
                skillset=skillset,
                item=SkillsetItem.objects.get(id=item_id),
                anzahl=quant,
            )

        messages.success(self.request, f"Gespeichert unter Medium {medium}!")
        context = self.get_common_context()
        context['saved_skillset'] = skillset
        return render(request, self.template_name, context)


class SkillsetEdit(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    queryset = Skillset.objects.prefetch_related(
        "item_relations__item",
    )
    permission_required = "ausleihe.change_skillset"
    pk_url_kwarg = "skillset_id"
    template_name_suffix = "_edit"
    form_class = SkillsetForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = SkillsetItem.objects.all()
        context['skills'] = Skill.objects.all()
        return context

    def save_new_item_relations(self):
        SkillsetItemRelation.objects.filter(skillset=self.object).delete()
        items = [
            (int(a), int(i))
            for a, i in zip(
                self.request.POST.getlist("item_quantities"),
                self.request.POST.getlist("item_ids")
            )
            if a and i
        ]
        for a, i in items:
            self.object.item_relations.create(anzahl=a, item_id=i)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        form = self.get_form()

        # Komischerweise verändert der Zugriff auf form.errors das medium von
        # self.object, deswegen müssen wir das hier schon zwischenspeichern.
        medium_alt = self.object.medium

        if "medium" in form.errors:
            del form.errors["medium"]

        if form.is_valid():
            medium_neu, created = Medium.objects.get_or_create(
                pk=form.data.get("medium")
            )
            if created:
                messages.warning(
                    request,
                    f"Es wurde das neue Medium {medium_neu} erzeugt."
                )

            self.object.medium = medium_neu
            self.object.name = form.cleaned_data["name"]
            self.object.skill = form.cleaned_data["skill"]
            self.object.save()

            self.save_new_item_relations()

            if not medium_alt.skillsets.exists():
                messages.warning(
                    request,
                    (f"Das alte Medium {medium_alt} hat keine Skill Sets mehr. "
                    "Bitte überprüfe das.")
                )

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class SkillsetDuplicate(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "ausleihe.change_skillset"

    def get(self, request, skillset_id):
        old_skillset_id = skillset_id
        old_skillset = get_object_or_404(Skillset, id=old_skillset_id)

        # Duplizieren:
        old_skillset.pk = None
        old_skillset.save()
        new_skillset_id = old_skillset.pk

        old_skillset = get_object_or_404(Skillset, id=old_skillset_id)
        new_skillset = get_object_or_404(Skillset, id=new_skillset_id)

        for r in old_skillset.item_relations.all():
            new_skillset.item_relations.create(anzahl=r.anzahl, item_id=r.item_id)

        messages.success(self.request, "Dupliziert! Hier kannst du es weiterbearbeiten.")
        return redirect("ausleihe:skillset-edit", skillset_id=new_skillset_id)


class SkillsetItemList(LoginRequiredMixin, ListView):
    queryset = SkillsetItem.objects.prefetch_related(
        "skillset_relations",
    )


class SkillsetItemCreate(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "ausleihe.add_skillsetitem"
    template_name = "ausleihe/skillsetitem_create.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        items = request.POST.get("items", "").strip().split("\r\n")
        new_items = []

        for item in items:
            new_item, created = SkillsetItem.objects.get_or_create(name=item)
            if created:
                new_items.append(new_item)

        context = {
            "new_items": new_items,
        }

        return render(request, self.template_name, context)


class SkillsetItemEdit(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SkillsetItem
    permission_required = "ausleihe.change_skillsetitem"
    fields = ["name", "beschreibung"]
    pk_url_kwarg = "skillsetitem_id"
    template_name_suffix = "_edit"

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:skillsetitem-list")


class SkillsetItemDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SkillsetItem
    permission_required = "ausleihe.delete_skillsetitem"
    pk_url_kwarg = "skillsetitem_id"
    success_url = reverse_lazy("ausleihe:skillsetitem-list")


class SkillList(LoginRequiredMixin, ListView):
    queryset = Skill.objects.prefetch_related(
        "raeume",
        "skillsets",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["raeume"] = Raum.objects.prefetch_related("skills")

        return context


class SkillDetail(LoginRequiredMixin, DetailView):
    queryset = Skill.objects.prefetch_related(
        "raeume",
        "skillsets",
    )
    pk_url_kwarg = "skill_id"


class SkillCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Skill
    permission_required = "ausleihe.add_skill"
    template_name_suffix = "_create"
    form_class = SkillForm

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:skill-list")


class SkillEdit(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Skill
    permission_required = "ausleihe.change_skill"
    form_class = SkillForm
    pk_url_kwarg = "skill_id"
    template_name_suffix = "_create"


class SkillReserve(LoginRequiredMixin, View):
    """
    Der Nutzer hat einen Skill gewählt und muss jetzt eine Verfügbarkeit (Raum mit
    Anfangs- und Endzeit) wählen.
    """
    template_name = "ausleihe/skill_reserve.html"

    def get_context_data(self, **kwargs):
        queryset = Skill.objects.prefetch_related("raeume")
        skill = get_object_or_404(queryset, pk=kwargs.get("skill_id"))

        v_tab = {}
        today = datetime.now(timezone.get_current_timezone()).date()
        vs = Verfuegbarkeit.objects.filter(
            datum__gte=today,
            raum__in=skill.raeume.all(),
        )
        raeume = sorted({v.raum for v in vs})

        for v in vs:
            if v.datum not in v_tab:
                v_tab[v.datum] = {raum: [] for raum in raeume}

            v_tab[v.datum][v.raum].append(v)

        context = {
            "skill": skill,
            "v_tab": v_tab,
            "raeume": raeume,
        }

        return context

    def get(self, request, skill_id):
        context = self.get_context_data(skill_id=skill_id)
        return render(request, self.template_name, context)


class SkillVerfuegbarkeitReserve(LoginRequiredMixin, View):
    """
    Der Nutzer hat einen Skill und eine Verfügbarkeit gewählt und muss jetzt eine
    konkrete Startzeit für die Reservierung wählen.
    """
    template_name = "ausleihe/skill_verfuegbarkeit_reserve.html"
    form_class = ReservierungszeitForm

    def get_context_data(self, **kwargs):
        skill = get_object_or_404(Skill, pk=kwargs.get("skill_id"))
        v = get_object_or_404(Verfuegbarkeit, id=kwargs.get("v_id"))
        fuser = FachschaftUser.objects.get(user=self.request.user)

        # Die letzte Zeit zum Reservieren ergibt sich aus
        # der Endzeit der Verfügbarkeit und der Dauer des Skills.
        dt_beginn = datetime.combine(v.datum, v.beginn)
        dt_ende = datetime.combine(v.datum, v.ende)
        v_ende = dt_ende - timedelta(minutes=skill.dauer)
        form = ReservierungszeitForm(verfuegbarkeit=v, v_ende=v_ende.time())

        td_15m = timedelta(minutes=15)
        # N ist die Anzahl der 15 min Zeitscheiben der verfügbaren Zeit:
        N = ceil((dt_ende - dt_beginn)/td_15m)

        auslastung = {
            timezone.make_aware(dt_beginn + n*td_15m): 0
            for n in range(N)
        }

        rs = Reservierung.objects.filter(
            skill=skill,
            raum=v.raum,
            zeit__gte=dt_beginn,
            ende__lte=dt_ende,
        )
        # K ist die Anzahl der 15 min Zeitscheiben, die der Skill benötigt:
        K = ceil(timedelta(minutes=skill.dauer) / td_15m)

        for r in rs:
            for i in range(K):
                auslastung[r.zeit + i*td_15m] += 1

        context = {
            "form": form,
            "fuser": fuser,
            "skill": skill,
            "v_ende": v_ende.time(),
            "verfuegbarkeit": v,
            "auslastung": auslastung,
            "n_skillsets": skill.skillsets.count(),
            "n_skillsets_1": skill.skillsets.count() - 1,
        }

        return context

    def get(self, request, skill_id, v_id):
        context = self.get_context_data(skill_id=skill_id, v_id=v_id)
        return render(request, self.template_name, context)

    def post(self, request, skill_id, v_id):
        context = self.get_context_data(skill_id=skill_id, v_id=v_id)

        form = ReservierungszeitForm(
            request.POST,
            verfuegbarkeit=context["verfuegbarkeit"],
            v_ende=context["v_ende"],
        )

        if form.is_valid():
            zeit = timezone.make_aware(
                datetime.combine(
                    context["verfuegbarkeit"].datum,
                    form.cleaned_data["zeit"]
                )
            )
        else:
            context["form"] = form
            return render(request, self.template_name, context)

        try:
            skill = context["skill"]
            skillset = choice(skill.available_skillsets(zeit))
        except IndexError as e:
            # kein Skillset verfügbar
            msg = (
                "Kein freies Skill Set zu dieser Zeit verfügbar. "
                "Wähle bitte eine andere Zeit."
            )
            form.add_error(None, msg)
            context["form"] = form
            return render(request, self.template_name, context)

        try:
            r = Reservierung(
                nutzer = context["fuser"],
                skill  = context["skill"],
                medium = skillset.medium,
                raum   = context["verfuegbarkeit"].raum,
                zeit   = zeit,
            )
            r.save()
        except ValidationError as e:
            form.add_error(None, e)
            context["form"] = form
            return render(request, self.template_name, context)

        return redirect("ausleihe:reservierung-detail", reservierung_id=r.id)


class ReservierungList(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    queryset = Reservierung.objects.filter(zeit__gte=timezone.localdate())
    permission_required = "ausleihe.change_reservierung"


class ReservierungDetail(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Reservierung
    pk_url_kwarg = "reservierung_id"

    def has_permission(self):
        user = self.request.user
        r = self.get_object()
        return user.fachschaftuser == r.nutzer


class ReservierungDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Reservierung
    pk_url_kwarg = "reservierung_id"
    success_url = reverse_lazy("ausleihe:home")

    def has_permission(self):
        user = self.request.user
        r = self.get_object()
        return user.fachschaftuser == r.nutzer


class ReservierungVerleihen(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "ausleihe.create_leihe"

    def get(self, request, reservierung_id):
        r = get_object_or_404(Reservierung, id=reservierung_id)

        if r.leihe:
            messages.warning(
                request,
                f"Reservierung wurde schon verliehen: {r.leihe}"
            )
        else:
            leihe = Leihe(
                medium=r.medium,
                nutzer=r.nutzer,
                anfang=timezone.now(),
                ende=r.ende,
                verleiht_von=request.user,
            )
            leihe.save()

            r.leihe = leihe
            r.save()

            messages.success(request, f"Verliehen: {leihe}")

        return redirect("ausleihe:reservierung-list")


class GebaeudeList(LoginRequiredMixin, ListView):
    model = Gebaeude


class GebaeudeCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Gebaeude
    permission_required = "ausleihe.add_gebaeude"
    template_name_suffix = "_create"
    form_class = GebaeudeForm

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:gebaeude-list")


class GebaeudeEdit(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Gebaeude
    permission_required = "ausleihe.change_gebaeude"
    form_class = GebaeudeForm
    pk_url_kwarg = "gebaeude_id"
    template_name_suffix = "_create"

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:gebaeude-list")


class RaumList(LoginRequiredMixin, ListView):
    model = Raum


class RaumCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Raum
    permission_required = "ausleihe.add_raum"
    template_name_suffix = "_create"
    form_class = RaumForm

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:raum-list")


class RaumEdit(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Raum
    permission_required = "ausleihe.change_raum"
    form_class = RaumForm
    pk_url_kwarg = "raum_id"
    template_name_suffix = "_create"

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:raum-list")


class RaumImport(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "ausleihe/raum_import.html"
    form_class = RaumImportForm
    permission_required = "ausleihe.add_raum"

    def get_success_url(self):
        return reverse("ausleihe:raum-list")

    def form_valid(self, form):
        url = form.clean_url()
        raum_id = form.raum_id
        anzahl_plaetze = form.cleaned_data["anzahl_plaetze"]

        r = requests.get(url)
        parser = LSFRoomParser()
        parser.feed(r.text)

        raum_name = parser.room_name

        raum = Raum.objects.create(
            name=raum_name,
            lsf_id=raum_id,
            anzahl_plaetze=anzahl_plaetze,
        )

        return super().form_valid(form)


class VerfuegbarkeitCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Verfuegbarkeit
    permission_required = "ausleihe.add_verfuegbarkeit"
    template_name_suffix = "_create"
    form_class = VerfuegbarkeitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.localdate()
        zeiten = Verfuegbarkeit.objects.filter(datum__gte=today)
        context["zeiten"] = zeiten

        return context

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:verfuegbarkeit-create")


class VerfuegbarkeitUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Verfuegbarkeit
    permission_required = "ausleihe.change_verfuegbarkeit"
    form_class = VerfuegbarkeitForm
    pk_url_kwarg = "v_id"
    template_name_suffix = "_form"

    def get_success_url(self):
        messages.success(self.request, "Gespeichert!")
        return reverse("ausleihe:verfuegbarkeit-create")


class VerfuegbarkeitDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Verfuegbarkeit
    permission_required = "ausleihe.delete_verfuegbarkeit"
    pk_url_kwarg = "v_id"
    success_url = reverse_lazy("ausleihe:verfuegbarkeit-create")
