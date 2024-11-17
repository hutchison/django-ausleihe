from django.db import models

from . import Gebaeude


class Raum(models.Model):
    name = models.CharField(max_length=200, unique=True)
    lsf_id = models.IntegerField(
        unique=True,
        verbose_name="LSF ID",
    )
    anzahl_plaetze = models.PositiveSmallIntegerField(
        verbose_name="Anzahl verfügbarer Plätze",
    )
    gebaeude = models.ForeignKey(
        Gebaeude,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="Gebäude",
        help_text=(
            "Das Gebäude ist für den komfortablen Import von Zeiten "
            "aus dem LSF erforderlich."
        ),
    )

    class Meta:
        verbose_name = "Raum"
        verbose_name_plural = "Räume"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

    def lsf_link(self):
        return f"https://lsf.uni-rostock.de/qisserver/rds?state=verpublish&status=init&vmfile=no&moduleCall=webInfo&publishConfFile=webInfoRaum&publishSubDir=raum&keep=y&raum.rgid={self.lsf_id}"

    def kurzname(self):
        return self.name.split(",")[0]

