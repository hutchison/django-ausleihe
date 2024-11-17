from django.conf import settings
from django.db import models
from django.utils import timezone

from fsmedhro_core.models import FachschaftUser

from . import Medium


class Leihe(models.Model):
    medium = models.ForeignKey(Medium, on_delete=models.PROTECT)
    nutzer = models.ForeignKey(
        FachschaftUser,
        on_delete=models.PROTECT,
        related_name='entliehen',
    )
    anfang = models.DateTimeField(auto_now=True)
    ende = models.DateTimeField()
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
        anfang = self.anfang.astimezone(timezone.get_current_timezone())
        ende = self.ende.astimezone(timezone.get_current_timezone())
        erzeugt = self.erzeugt.astimezone(timezone.get_current_timezone())
        return (
            f"{self.medium} an {self.nutzer} "
            f"({anfang:%d.%m.%Y %H:%M} – {ende:%d.%m.%Y %H:%M}) "
            f"durch {self.verleiht_von} am {erzeugt:%d.%m.%Y %H:%M} {r}"
        )

    def ist_ueberfaellig(self):
        return timezone.now() > self.ende

    def differenz_heute(self):
        return abs((timezone.now() - self.ende).days)

    def dauer(self):
        return (self.ende - self.anfang).days

