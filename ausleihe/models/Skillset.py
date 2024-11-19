from django.db import models
from django.shortcuts import reverse


class Skillset(models.Model):
    name = models.CharField(max_length=200)

    medium = models.ForeignKey(
        "ausleihe.Medium",
        on_delete=models.PROTECT,
        related_name="skillsets",
    )
    skill = models.ForeignKey(
        "ausleihe.Skill",
        on_delete=models.PROTECT,
        related_name="skillsets",
    )

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"<Skillset: name={self.name}, medium={self.medium}, skill={self.skill}>"

    class Meta:
        verbose_name = "Skillset"
        verbose_name_plural = "Skillsets"
        ordering = ("name",)

    def get_absolute_url(self):
        return reverse("ausleihe:skillset-detail", kwargs={"skillset_id": self.id})

