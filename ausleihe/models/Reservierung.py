from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone

from fsmedhro_core.models import FachschaftUser

from . import Skill, Medium, Raum, Leihe


class Reservierung(models.Model):
    nutzer = models.ForeignKey(
        FachschaftUser,
        on_delete=models.PROTECT,
        related_name="reservierungen",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name="reservierungen",
    )
    medium = models.ForeignKey(
        Medium,
        on_delete=models.PROTECT,
        related_name="reservierungen",
    )
    raum = models.ForeignKey(
        Raum,
        on_delete=models.PROTECT,
        related_name="reservierungen",
    )
    leihe = models.OneToOneField(
        Leihe,
        on_delete=models.PROTECT,
        related_name="reservierung",
        blank=True,
        null=True,
        help_text=(
            "Wenn eine Reservierung wirklich ausgeliehen wurde, "
            "wird hier die Leihe verlinkt."
        ),
    )
    zeit = models.DateTimeField(
        verbose_name="Datum und Uhrzeit",
        help_text="Für wann gilt die Reservierung?",
    )
    ende = models.DateTimeField(
        editable=False,
    )
    erzeugt = models.DateTimeField(auto_now=True)

    @property
    def lokale_zeit(self):
        return self.zeit.astimezone(timezone.get_current_timezone())

    @property
    def lokales_ende(self):
        return self.ende.astimezone(timezone.get_current_timezone())

    class Meta:
        verbose_name = "Reservierung"
        verbose_name_plural = "Reservierungen"
        ordering = ("zeit", "nutzer", "skill", "medium", "raum")

    def __str__(self):
        return (
            f"{self.nutzer}; "
            f"{self.skill}; "
            f"{self.medium}; "
            f"{self.raum}; "
            f"{self.lokale_zeit:%d.%m.%Y · %H:%M}"
            "-"
            f"{self.lokales_ende:%H:%M}"
        )

    def _skill_im_raum(self):
        """
        Kann der Skill dem Raum durchgeführt werden?
        """
        return self.skill in self.raum.skills.all()

    def _skill_vom_medium(self):
        """
        Kann der Skill mit dem Medium durchgeführt werden?
        Ein Medium kann mehrere Skillsets haben, die jeweils einen Skill abdecken.
        Deckt irgendein Skillset den Skill ab, den wir reservieren wollen?
        """
        return any(
            self.skill == sk_set.skill
            for sk_set
            in self.medium.skillsets.all()
        )

    def _raum_zeitlich_verfuegbar(self):
        """
        Ist der Raum zeitlich verfügbar?
        Bietet der Raum zur gewünschten Zeit eine verfügbare Zeit an?
        """

        # datetime wird immer mit TZ=UTC gespeichert, also muss ich das hier umrechnen:
        lz = self.lokale_zeit

        # Der Raum ist zeitlich verfügbar, wenn
        # * das Datum stimmt
        # * der Beginn der Verfügbarkeit <= der Reservierungszeit ist
        # * das Ende der Verfügbarkeit >= der Reservierungszeit + Skilldauer ist
        return self.raum.verfuegbarkeiten.filter(
            datum=lz.date(),
            beginn__lte=lz.time(),
            ende__gte=(lz + timedelta(minutes=self.skill.dauer))
        ).exists()

    @staticmethod
    def _Q_ueberschneidungen(von, bis):
        """
        Hier müssen wir herausfinden, welche Reservierungen sich der eigenen Zeit (von,
        bis) überschneiden bzw. welche Sonderfälle wir ausschließen müssen.

        zeit ist die Anfangszeit der Reservierung, ende = zeit + skill.dauer

        Folgende Fälle können auftreten:

            zeit       von     bis      ende
                        [-------)
        1           [-------)
        2                   [-------)
        3                 [---)                 (wird von 1 und 2 schon abgedeckt)
        4           [---------------)
        5           [---)                       (keine Überschneidung)
        6                       [---)           (keine Überschneidung)
        """
        return (
            Q(zeit__lte = von, ende__gt  = von) |    # Fall 1
            Q(zeit__lt  = bis, ende__gte = bis) |    # Fall 2
            Q(zeit__lte = von, ende__gte = bis)      # Fall 4
        )

    def Q_ueberschneidungen(self):
        von, bis = self.zeit, self.zeit + timedelta(minutes=self.skill.dauer)
        return self._Q_ueberschneidungen(von, bis)

    def _ueberschneidende_reservierungen_vom_raum(self):
        return self.raum.reservierungen.filter(
            self.Q_ueberschneidungen()
        ).exclude(
            id=self.id,
        )

    def _raum_hat_kapazitaet(self):
        r = self._ueberschneidende_reservierungen_vom_raum()
        if r.exists():
            # gehe alle überschneidenden Reservierungen zu diesem Raum durch und
            # summiere die benötigten Plätze der Skills
            r_plaetze = r.annotate(
                anzahl_plaetze=Sum("skill__anzahl_plaetze")
            ).first()

            l = r_plaetze.anzahl_plaetze if r_plaetze else 0
            kapazitaet = self.raum.anzahl_plaetze - l

            return kapazitaet >= self.skill.anzahl_plaetze
        else:
            return self.raum.anzahl_plaetze     # True <=> (> 0)

    def _ueberschneidende_reservierungen_vom_medium(self):
        return self.medium.reservierungen.filter(
            self.Q_ueberschneidungen()
        ).exclude(
            medium=self.medium
        )

    def _medium_zeitlich_verfuegbar(self):
        # Für das eigene Medium darf keine Reservierung in diesem Zeitraum existieren:
        return not self._ueberschneidende_reservierungen_vom_medium().exists()

    def _ueberschneidende_reservierungen_von_nutzer(self):
        return self.nutzer.reservierungen.filter(
            self.Q_ueberschneidungen()
        ).exclude(
            id=self.id,
        )

    def clean(self):
        if not self._skill_im_raum():
            raise ValidationError(
                "Skill wird in dem Raum nicht angeboten."
            )

        if not self._skill_vom_medium():
            raise ValidationError(
                f'Skill "{self.skill.name}" wird vom '
                f'Medium "{self.medium}" nicht angeboten.'
            )

        if not self._raum_zeitlich_verfuegbar():
            raise ValidationError(
                "Der Raum bietet für diese Zeit keine verfügbare Zeit an."
            )

        if not self._raum_hat_kapazitaet():
            raise ValidationError(
                "Dieser Raum hat zu dieser Zeit nicht genügend freie Plätze."
            )

        if not self._medium_zeitlich_verfuegbar():
            raise ValidationError(
                "Das Medium ist in diesem Zeiraum schon reserviert."
            )

        if self._ueberschneidende_reservierungen_von_nutzer():
            r = self._ueberschneidende_reservierungen_von_nutzer().get()
            raise ValidationError(
                "Du hast in diesem Zeitraum schon einen anderen Skill reserviert: "
                f"{r.skill} von {r.lokale_zeit:%H:%M}"
                " – "
                f"{r.lokales_ende:%H:%M} Uhr"
            )


    def save(self, *args, **kwargs):
        self.full_clean()  # ruft u.a. self.clean() auf
        self.ende = self.zeit + timedelta(minutes=self.skill.dauer)
        super().save(*args, **kwargs)
