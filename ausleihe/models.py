from datetime import date, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.shortcuts import reverse
from django.utils import timezone

from fsmedhro_core.models import FachschaftUser


class Medium(models.Model):
    """
    Ein Medium kann alles mögliche sein, aber es hat immer einen eindeutigen
    Bezeichner. Dieser Bezeichner ist hier ein String, da bereits existierende Bücher
    Barcodeaufkleber mit Bezeichnern wie z.B. '00950' haben.
    """
    id = models.CharField(max_length=100, primary_key=True, verbose_name="Bezeichner")

    class Meta:
        verbose_name = "Medium"
        verbose_name_plural = "Medien"
        ordering = ("id",)

    def __str__(self):
        return self.id

    def aktuell_ausgeliehen(self):
        return self.leihe_set.filter(
            anfang__lte=date.today(),   # anfang <= today <= ende
            ende__gte=date.today(),
            zurueckgebracht=False,
        ).exists()


class Leihe(models.Model):
    medium = models.ForeignKey(Medium, on_delete=models.PROTECT)
    nutzer = models.ForeignKey(
        FachschaftUser,
        on_delete=models.PROTECT,
        related_name='entliehen',
    )
    anfang = models.DateField(auto_now=True)
    ende = models.DateField()
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
        return (
            f"{self.medium} an {self.nutzer} "
            f"({self.anfang} – {self.ende}) "
            f"durch {self.verleiht_von} am {self.erzeugt} {r}"
        )

    def ist_ueberfaellig(self):
        return date.today() > self.ende

    def differenz_heute(self):
        return abs((date.today() - self.ende).days)

    def dauer(self):
        return (self.ende - self.anfang).days


class Autor(models.Model):
    vorname = models.CharField(max_length=100, blank=True)
    nachname = models.CharField(max_length=200)

    def __str__(self):
        return " ".join([self.vorname, self.nachname])

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autoren"
        ordering = ("nachname", "vorname")


class Verlag(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Verlag"
        verbose_name_plural = "Verlage"
        ordering = ("name",)


class Buch(models.Model):
    titel = models.CharField(max_length=300)
    isbn = models.CharField(max_length=17, verbose_name="ISBN", blank=True)
    ausgabe = models.CharField(max_length=50, blank=True)
    beschreibung = models.TextField(blank=True)

    medium = models.ForeignKey(
        Medium,
        on_delete=models.PROTECT,
        related_name="buecher",
    )
    verlag = models.ForeignKey(
        Verlag,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="buecher",
    )
    autoren = models.ManyToManyField(
        Autor,
        related_name="buecher",
    )

    class Meta:
        verbose_name = "Buch"
        verbose_name_plural = "Bücher"
        ordering = ("medium", "titel")

    def __str__(self):
        return self.titel

    @staticmethod
    def dict_from_post_data(post_data):
        buch = {
            "ausgabe": post_data.get("ausgabe", "").strip(),
            "beschreibung": post_data.get("beschreibung", "").strip(),
            "isbn": post_data.get("isbn", "").replace("-", "").strip(),
            "medium_id": post_data.get("medium_id", "").strip(),
            "titel": post_data.get("titel", "").strip(),
            "verlag_id": post_data.get("verlag"),
        }

        v = None
        if buch["verlag_id"]:
            v = Verlag.objects.get(id=int(buch["verlag_id"]))
        buch["verlag"] = v

        return buch


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

    def lsf_link(self):
        return f"https://lsf.uni-rostock.de/qisserver/rds?state=verpublish&status=init&vmfile=no&moduleCall=webInfo&publishConfFile=webInfoRaum&publishSubDir=raum&keep=y&raum.rgid={self.lsf_id}"

    def kapazitaet(self, von, bis):
        """
        Hier müssen wir herausfinden, welche Reservierungen sich mit von und bis
        überschneiden bzw. welche Sonderfälle wir ausschließen müssen.

        zeit ist die Anfangszeit der Reservierung, ende = zeit + skill.dauer

        Folgende Fälle können auftreten:

            zeit       von     bis      ende
                        |-------|
        1           |-------|
        2                   |-------|
        3                 |---|                 (wird von 1 und 2 schon abgedeckt)
        4           |---------------|
        5           |---|
        6                       |---|

        """
        res = Reservierung.objects.filter(
            raum=self,
        ).filter(
            Q(zeit__lte=von, ende__gt=von)  |    # Fall 1
            Q(zeit__lt=bis,  ende__gte=bis) |    # Fall 2
            Q(zeit__lte=von, ende__gte=bis)      # Fall 4
        ).annotate(
            anzahl_plaetze=Sum("skill__anzahl_plaetze")
        ).first()

        l = 0
        if res:
            l = res.anzahl_plaetze

        return self.anzahl_plaetze - l


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


class Skill(models.Model):
    nummer = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=200, unique=True)
    anzahl_plaetze = models.PositiveSmallIntegerField(
        verbose_name="Anzahl benötigter Plätze",
        help_text="Wie viele Plätze werden von den vorhandenen Plätzen eines Raumes benötigt?"
    )
    min_personen = models.PositiveSmallIntegerField(
        verbose_name="Mind. Personen",
        help_text="Wie viele Personen werden mindestens für die Durchführung benötigt?"
    )
    max_personen = models.PositiveSmallIntegerField(
        verbose_name="Max. Personen",
        help_text="Wie viele Personen können maximal an der Durchführung beteilgt sein?"
    )
    dauer = models.PositiveSmallIntegerField(
        help_text="Zeitraum (min)"
    )
    beschreibung = models.TextField(blank=True)
    raeume = models.ManyToManyField(
        Raum,
        related_name="skills",
        verbose_name="Räume",
        help_text="In welchen Räumen kann dieser Skill durchgeführt werden?",
        blank=True,
    )

    class Meta:
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
        ordering = ("nummer",)

    def __str__(self):
        return f"Skill Nr. {self.nummer}: {self.name}"

    def get_absolute_url(self):
        return reverse("ausleihe:skill-detail", kwargs={"skill_id": self.id})


class SkillsetItem(models.Model):
    name = models.CharField(max_length=200, unique=True)
    beschreibung = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Skillset Item"
        verbose_name_plural = "Skillset Items"
        ordering = ("name",)


class Skillset(models.Model):
    name = models.CharField(max_length=200)

    medium = models.ForeignKey(
        Medium,
        on_delete=models.PROTECT,
        related_name="skillsets",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name="skillsets",
    )

    def __str__(self):
        return f"{self.name} ({self.id})"

    class Meta:
        verbose_name = "Skillset"
        verbose_name_plural = "Skillsets"
        ordering = ("name",)

    @staticmethod
    def dict_from_post_data(post_data):
        skillset = {
            "medium_id": post_data.get("medium_id", "").strip(),
            "name": post_data.get("name", "").strip(),
            "skill_id": int(post_data.get("skill", "").strip()),
            "beschreibung": post_data.get("beschreibung", "").strip(),
            "items": [
                (int(q), int(i))
                for q, i in zip(
                    post_data.getlist("item_quantities"),
                    post_data.getlist("item_ids")
                )
                if q and i
            ],
        }

        return skillset


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
    raum = models.ForeignKey(
        Raum,
        on_delete=models.PROTECT,
        related_name="reservierungen",
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
        ordering = ("-zeit", "nutzer", "skill", "raum")

    def __str__(self):
        return (
            f"{self.nutzer}; "
            f"{self.skill}; "
            f"{self.raum}; "
            f"{self.lokale_zeit:%d.%m.%Y · %H:%M}"
            "-"
            f"{self.lokales_ende:%H:%M}"
        )

    def clean(self):
        # Kann der Skill dem Raum durchgeführt werden?
        if self.skill not in self.raum.skills.all():
            raise ValidationError("Skill wird in dem Raum nicht angeboten.")

        # Ist der Raum zeitlich verfügbar?
        # Bietet der Raum zur gewünschten Zeit eine verfügbare Zeit an?

        # datetime wird immer mit TZ=UTC gespeichert, also muss ich das hier umrechnen:
        lz = self.lokale_zeit
        # Der Raum ist zeitlich verfügbar, wenn
        # * das Datum stimmt
        # * der Beginn der Verfügbarkeit <= der Reservierungszeit ist
        # * das Ende der Verfügbarkeit >= der Reservierungszeit + Skilldauer ist
        raum_ist_zeitlich_verfuegbar = self.raum.verfuegbarkeiten.filter(
            datum=lz.date(),
            beginn__lte=lz.time(),
            ende__gte=(lz + timedelta(minutes=self.skill.dauer))
        ).exists()
        if not raum_ist_zeitlich_verfuegbar:
            raise ValidationError(
                "Der Raum bietet für diese gewünschte Zeit keine verfügbare Zeit an."
            )

        # Hat der Raum zu dieser Zeit genügend Kapazität (freie Plätze)?
        von = self.zeit
        bis = self.zeit + timedelta(minutes=self.skill.dauer)
        if not self.raum.kapazitaet(von, bis):
            raise ValidationError(
                "Dieser Raum hat zu dieser Zeit nicht genügend freie Plätze."
            )

        # Gibt es ein freies Medium, das dafür verliehen werden kann?


    def save(self, *args, **kwargs):
        self.clean()
        self.ende = self.zeit + timedelta(minutes=self.skill.dauer)
        super().save(*args, **kwargs)
