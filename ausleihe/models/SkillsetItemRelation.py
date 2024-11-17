from django.db import models

from . import Skillset, SkillsetItem


class SkillsetItemRelation(models.Model):
    skillset = models.ForeignKey(
        Skillset,
        on_delete=models.CASCADE,
        related_name="item_relations"
    )
    item = models.ForeignKey(
        SkillsetItem,
        on_delete=models.CASCADE,
        related_name="skillset_relations"
    )
    anzahl = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.skillset.name} - {self.item.name}: {self.anzahl}"

    class Meta:
        verbose_name = "Skillset-Item Relation"
        verbose_name_plural = "Skillset-Item Relationen"
        ordering = ("skillset", "item")
        unique_together = ["skillset", "item"]
