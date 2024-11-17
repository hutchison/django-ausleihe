from django.db import models


class Autor(models.Model):
    vorname = models.CharField(max_length=100, blank=True)
    nachname = models.CharField(max_length=200)

    def __str__(self):
        return " ".join([self.vorname, self.nachname])

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autoren"
        ordering = ("nachname", "vorname")
