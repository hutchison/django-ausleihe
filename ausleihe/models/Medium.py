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
        ordering = ("id",)

    def __str__(self):
        return self.id

    def aktuell_ausgeliehen(self):
        return self.leihe_set.filter(
            anfang__lte=timezone.now(),   # anfang <= today <= ende
            ende__gte=timezone.now(),
            zurueckgebracht=False,
        ).exists()

