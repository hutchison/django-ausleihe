from django.db import models


class Gebaeude(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Bitte benenne Gebäude immer so, wie sie auch im LSF heißen.",
    )
    lsf_id = models.IntegerField(
        unique=True,
        verbose_name="LSF ID",
        help_text="Die LSF ID steht in der URL (z.B. k_gebaeude.gebid=101)."
    )

    class Meta:
        verbose_name = "Gebäude"
        verbose_name_plural = "Gebäude"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def lsf_link(self):
        return f"https://lsf.uni-rostock.de/qisserver/rds?state=verpublish&publishContainer=buildingContainer&k_gebaeude.gebid={self.lsf_id}"

