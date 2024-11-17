from django.db import models

from . import Autor, Verlag, Medium


class Buch(models.Model):
    titel = models.CharField(max_length=300)
    isbn = models.CharField(max_length=17, verbose_name="ISBN", blank=True)
    ausgabe = models.CharField(max_length=50, blank=True)
    beschreibung = models.TextField(blank=True)

    medium = models.ForeignKey(
        Medium,
        on_delete=models.PROTECT,
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

