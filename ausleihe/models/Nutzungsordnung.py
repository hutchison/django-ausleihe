from pathlib import Path

from django.conf import settings
from django.db import models


def datierte_nutzungsordnung(instance, filename):
    fn = f"{instance.erzeugt:%Y-%m-%d}_Nutzungsordnung.pdf"
    return f"ausleihe/nutzungsordnungen/{fn}"


class Nutzungsordnung(models.Model):
    erzeugt = models.DateTimeField(auto_now=True)
    datei = models.FileField(
        upload_to=datierte_nutzungsordnung,
    )
    akzeptiert_von = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="akzeptierte_nutzungsordnungen",
        blank=True,
    )

    class Meta:
        verbose_name = "Nutzungsordnung"
        verbose_name_plural = "Nutzungsordnungen"
        ordering = ("-erzeugt",)

    def __str__(self):
        return f"Nutzungsordnung: {self.datei.name} ({self.erzeugt})"

    def __repr__(self):
        return f"<Nutzungsordnung: {self.datei.name} ({self.erzeugt})>"

    @property
    def datei_name(self):
        return Path(self.datei.name).name
