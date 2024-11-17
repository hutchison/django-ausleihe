from django.db import models


class Verlag(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Verlag"
        verbose_name_plural = "Verlage"
        ordering = ("name",)
