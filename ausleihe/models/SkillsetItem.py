from django.db import models


class SkillsetItem(models.Model):
    name = models.CharField(max_length=200, unique=True)
    beschreibung = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Skillset Item"
        verbose_name_plural = "Skillset Items"
        ordering = ("name",)
