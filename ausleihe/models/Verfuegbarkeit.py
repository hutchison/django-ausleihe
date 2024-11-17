from django.core.exceptions import ValidationError
from django.db import models

from . import Raum


class Verfuegbarkeit(models.Model):
    datum = models.DateField()
    beginn = models.TimeField()
    ende = models.TimeField()
    raum = models.ForeignKey(
        Raum,
        on_delete=models.CASCADE,
        related_name="verfuegbarkeiten",
    )
    notiz = models.TextField(
        blank=True,
    )

    class Meta:
        verbose_name = "Verfügbarkeit"
        verbose_name_plural = "Verfügbarkeiten"
        ordering = ("datum", "beginn", "raum")

    def __str__(self):
        return (
            f"{self.raum}: "
            f"{self.datum:%d.%m.%Y} · "
            f"{self.beginn:%H:%M}"
            " - "
            f"{self.ende:%H:%M}"
            " Uhr"
        )

    def clean(self):
        if self.beginn > self.ende:
            raise ValidationError("Es muss Beginn < Ende gelten.")

        ueberschneidung_kandidaten = Verfuegbarkeit.objects.filter(
            datum=self.datum,
            raum=self.raum,
        ).exclude(
            id=self.id,
        )

        ueberschneidung_beginn = ueberschneidung_kandidaten.filter(
            beginn__lte=self.beginn,
            ende__gte=self.beginn,
        )
        if ueberschneidung_beginn.exists():
            u = "; ".join(map(str, ueberschneidung_beginn))
            raise ValidationError(
                f"Der Beginn überschneidet sich mit: {u}"
            )

        ueberschneidung_ende = ueberschneidung_kandidaten.filter(
            beginn__lte=self.ende,
            ende__gte=self.ende,
        )
        if ueberschneidung_ende.exists():
            u = "; ".join(map(str, ueberschneidung_ende))
            raise ValidationError(
                f"Das Ende überschneidet sich mit: {u}"
            )

        ueberschneidung_beide = ueberschneidung_kandidaten.filter(
            beginn__gte=self.beginn,
            ende__lte=self.ende,
        )
        if ueberschneidung_beide.exists():
            u = "; ".join(map(str, ueberschneidung_beide))
            raise ValidationError(
                f"Die Zeit überschneidet sich mit: {u}"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

