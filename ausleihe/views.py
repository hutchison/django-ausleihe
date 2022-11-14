from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.utils.http import urlencode
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from datetime import date, datetime, timedelta
from fsmedhro_core.models import FachschaftUser

from .models import (
    Autor,
    Buch,
    Leihe,
    Medium,
    Verlag,
)


class Home(LoginRequiredMixin, View):
    def get(self, request):
        fuser = FachschaftUser.objects.get(user=request.user)
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

        return render(request, "ausleihe/home.html", context)


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
        context = {
            "medien": Medium.objects.all(),
            "nutzer": FachschaftUser.objects.prefetch_related("user").order_by(
                "user__last_name",
                "user__first_name",
            ),
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


class LeiheList(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "ausleihe.view_leihe"
    queryset = Leihe.objects.prefetch_related(
        "medium",
        "nutzer",
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
        fuser = get_object_or_404(FachschaftUser, user=user.id)

        leihen = Leihe.objects.filter(nutzer=fuser)

        context = {
            "nutzer": fuser,
            "aktuell_verliehen": leihen.filter(zurueckgebracht=False),
            "historisch_verliehen": leihen.filter(zurueckgebracht=True),
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
