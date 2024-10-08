from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.http import urlencode
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from datetime import date, datetime, timedelta
from fsmedhro_core.models import FachschaftUser, Kontaktdaten

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


class Home(LoginRequiredMixin, View):
    template_name = "ausleihe/home.html"

    def get(self, request):
        try:
            fuser = FachschaftUser.objects.get(user=request.user)
        except FachschaftUser.DoesNotExist:
            return render(request, "ausleihe/profil_unvollstaendig.html")
        else:
            aktuell_verliehen = Leihe.objects.prefetch_related(
                "medium__buecher",
            ).filter(
                zurueckgebracht=False,
                nutzer=fuser,
            )

            historisch_verliehen = Leihe.objects.prefetch_related(
                "medium__buecher",
            ).filter(
                zurueckgebracht=True,
                nutzer=fuser,
            )

            context = {
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
            "anfang": date.today(),
            "ende": date.today() + timedelta(days=30),
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
        anfang = date.fromisoformat(request.POST.get("anfang"))
        ende = date.fromisoformat(request.POST.get("ende"))

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
            ende=date.today(),
        )

        username = request.GET.get("username", None)
        if username:
            # umleiten zu verliehen-an:
            url = reverse("ausleihe:verliehen-an")
            parameter = urlencode({"username": username})
            return redirect(f"{url}?{parameter}")
        else:
            return redirect("ausleihe:verliehen")


class LeiheList(LoginRequiredMixin, ListView):
    queryset = Leihe.objects.prefetch_related(
        "medium",
        "medium__buecher",
        "nutzer__user",
        "verleiht_von",
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
    model = Skillset
    pk_url_kwarg = "skillset_id"


class SkillsetCreate(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "ausleihe.create_skillset"
    template_name = "ausleihe/skillset_create.html"

    def get_common_context(self):
        context = {
            "items": SkillsetItem.objects.all(),
        }
        return context

    def get(self, request):
        context = self.get_common_context()
        return render(request, self.template_name, context)

    def post(self, request):
        medium_id = request.POST.get("medium_id")
        name = request.POST.get("name")
        beschreibung = request.POST.get("beschreibung")
        item_quantities = request.POST.getlist("item_quantities")
        item_ids = request.POST.getlist("item_ids")

        medium, created = Medium.objects.get_or_create(pk=medium_id)
        skillset = Skillset.objects.create(
            medium=medium,
            name=name,
            beschreibung=beschreibung,
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
    model = Skillset
    permission_required = "ausleihe.change_skillset"
    fields = ["medium", "name", "beschreibung"]
    pk_url_kwarg = "skillset_id"
    template_name_suffix = "_edit"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = SkillsetItem.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        skillset_neu = Skillset.dict_from_post_data(request.POST)

        medium_alt = self.object.medium
        medium, created = Medium.objects.get_or_create(pk=skillset_neu["medium_id"])
        if created:
            messages.warning(
                request,
                f"Es wurde das neue Medium {medium} erzeugt."
            )

        self.object.medium = medium
        self.object.name = skillset_neu["name"]
        self.object.beschreibung = skillset_neu["beschreibung"]

        self.object.save()

        SkillsetItemRelation.objects.filter(skillset=self.object).delete()
        for q, i in skillset_neu["items"]:
            self.object.item_relations.create(anzahl=q, item_id=i)

        if not medium_alt.skillsets.exists():
            messages.warning(
                request,
                (f"Das alte Medium {medium_alt} hat keine Skillsets mehr. "
                 "Bitte überprüfe das.")
            )

        return redirect('ausleihe:skillset-detail', skillset_id=self.object.id)


class SkillsetItemList(LoginRequiredMixin, ListView):
    queryset = SkillsetItem.objects.prefetch_related(
        "skillset_relations",
    )


class SkillsetItemCreate(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = "ausleihe/skillsetitem_create.html"
    permission_required = "ausleihe.create_skillsetitem"

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
