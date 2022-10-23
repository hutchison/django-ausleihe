from django.db import models


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

    def __str__(self):
        return self.id


class BuchAutor(models.Model):
    vorname = models.CharField(max_length=100, blank=True)
    nachname = models.CharField(max_length=200)

    def __str__(self):
        return " ".join([self.vorname, self.nachname])

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autoren"
        ordering = ("nachname", "vorname")


class Buch(models.Model):
    titel = models.CharField(max_length=300)
    isbn = models.CharField(max_length=17, verbose_name="ISBN", blank=True)
    verlag = models.CharField(max_length=200, blank=True)
    ausgabe = models.CharField(max_length=50, blank=True)
    beschreibung = models.TextField(blank=True)

    medium = models.ForeignKey(Medium, on_delete=models.CASCADE)
    autoren = models.ManyToManyField(BuchAutor, related_name="buecher")

    class Meta:
        verbose_name = "Buch"
        verbose_name_plural = "Bücher"

    def __str__(self):
        return self.titel
