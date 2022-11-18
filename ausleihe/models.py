from django.conf import settings
from django.db import models
from datetime import date

from fsmedhro_core.models import FachschaftUser


class Medium(models.Model):
    """
    Ein Medium kann alles mögliche sein, aber es hat immer einen eindeutigen
    Bezeichner. Dieser Bezeichner ist hier ein String, da bereits existierende Bücher
    Barcodeaufkleber mit Bezeichnern wie z.B. '00950' haben.
    """
    id = models.CharField(max_length=100, primary_key=True, verbose_name="Bezeichner")

    class Meta:
        verbose_name = "Medium"
        verbose_name_plural = "Medien"
        ordering = ("id",)

    def __str__(self):
        return self.id

    def aktuell_ausgeliehen(self):
        return self.leihe_set.filter(
            anfang__lte=date.today(),   # anfang <= today <= ende
            ende__gte=date.today(),
            zurueckgebracht=False,
        ).exists()


class Autor(models.Model):
    vorname = models.CharField(max_length=100, blank=True)
    nachname = models.CharField(max_length=200)

    def __str__(self):
        return " ".join([self.vorname, self.nachname])

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autoren"
        ordering = ("nachname", "vorname")


class Verlag(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Verlag"
        verbose_name_plural = "Verlage"
        ordering = ("name",)


class Buch(models.Model):
    titel = models.CharField(max_length=300)
    isbn = models.CharField(max_length=17, verbose_name="ISBN", blank=True)
    ausgabe = models.CharField(max_length=50, blank=True)
    beschreibung = models.TextField(blank=True)

    medium = models.ForeignKey(
        Medium,
        on_delete=models.CASCADE,
        related_name="buecher",
    )
    verlag = models.ForeignKey(
        Verlag,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="buecher",
    )
    autoren = models.ManyToManyField(
        Autor,
        related_name="buecher",
    )

    class Meta:
        verbose_name = "Buch"
        verbose_name_plural = "Bücher"
        ordering = ("medium", "titel")

    def __str__(self):
        return self.titel

    @staticmethod
    def dict_from_post_data(post_data):
        buch = {
            "ausgabe": post_data.get("ausgabe", "").strip(),
            "beschreibung": post_data.get("beschreibung", "").strip(),
            "isbn": post_data.get("isbn", "").replace("-", "").strip(),
            "medium_id": post_data.get("medium_id", "").strip(),
            "titel": post_data.get("titel", "").strip(),
            "verlag_id": post_data.get("verlag"),
        }

        v = None
        if buch["verlag_id"]:
            v = Verlag.objects.get(id=int(buch["verlag_id"]))
        buch["verlag"] = v

        return buch


class Leihe(models.Model):
    medium = models.ForeignKey(Medium, on_delete=models.PROTECT)
    nutzer = models.ForeignKey(
        FachschaftUser,
        on_delete=models.PROTECT,
        related_name='entliehen',
    )
    anfang = models.DateField(auto_now=True)
    ende = models.DateField()
    zurueckgebracht = models.BooleanField(default=False, verbose_name="zurückgebracht")
    erzeugt = models.DateTimeField(auto_now=True)
    verleiht_von = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='verliehen',
    )

    class Meta:
        verbose_name = "Leihe"
        verbose_name_plural = "Leihen"
        ordering = ("-ende",)

    def __str__(self):
        r = "✓" if self.zurueckgebracht else "✗"
        return (
            f"{self.medium} an {self.nutzer} "
            f"({self.anfang} – {self.ende}) "
            f"durch {self.verleiht_von} am {self.erzeugt} {r}"
        )

    def ist_ueberfaellig(self):
        return date.today() > self.ende

    def differenz_heute(self):
        return abs((date.today() - self.ende).days)

    def dauer(self):
        return (self.ende - self.anfang).days
