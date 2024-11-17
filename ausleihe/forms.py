import re
from datetime import datetime, timedelta

from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Column,
    Div,
    Field,
    HTML,
    Layout,
    Row,
    Submit,
)
from crispy_forms.bootstrap import (
    InlineCheckboxes,
)

from .models import (
    Gebaeude,
    Raum,
    Reservierung,
    Skill,
    Skillset,
    Verfuegbarkeit,
)


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = [
            "nummer",
            "name",
            "anzahl_plaetze",
            "min_personen",
            "max_personen",
            "dauer",
            "beschreibung",
            "raeume",
        ]
        widgets = {
            "raeume": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "skill"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Speichern"))
        self.helper.layout = Layout(
            Row(
                Column(
                    Field("nummer"),
                    css_class="col-3",
                ),
                Column(
                    Field("name"),
                ),
            ),
            Row(
                Column(
                    Field("anzahl_plaetze"),
                ),
                Column(
                    Field("min_personen"),
                ),
                Column(
                    Field("max_personen"),
                ),
                Column(
                    Field("dauer"),
                ),
            ),
            Row(
                Column(
                    Field("beschreibung"),
                ),
            ),
            Row(
                Column(
                    InlineCheckboxes("raeume"),
                ),
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        min_personen = cleaned_data.get("min_personen")
        max_personen = cleaned_data.get("max_personen")

        if min_personen > max_personen:
            raise ValidationError(
                "Die Mindestanzahl an Personen darf nicht größer sein als die "
                "maximale Anzahl von benötigten Personen."
            )


class SkillsetForm(forms.ModelForm):
    class Meta:
        model = Skillset
        fields = ["medium", "name", "skill"]
        widgets = {
            "medium": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("medium"),
            Field("name"),
            Field("skill"),
            Submit("submit", "Speichern"),
        )


class GebaeudeForm(forms.ModelForm):
    class Meta:
        model = Gebaeude
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "gebaeude"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Speichern"))
        self.helper.layout = Layout(
            Row(
                Column(
                    Field("name"),
                ),
                Column(
                    Field("lsf_id"),
                ),
            ),
        )


class RaumForm(forms.ModelForm):
    class Meta:
        model = Raum
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "raum"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Speichern"))
        self.helper.layout = Layout(
            Row(
                Column(
                    Field("name"),
                ),
                Column(
                    Field("gebaeude"),
                ),
            ),
            Row(
                Column(
                    Field("lsf_id"),
                ),
                Column(
                    Field("anzahl_plaetze"),
                ),
            ),
        )


class RaumImportForm(forms.Form):
    url = forms.URLField(
        label="LSF URL",
        help_text="Öffne einen Raum im LSF und kopiere die URL hier rein."
    )
    anzahl_plaetze = forms.IntegerField(
        label="Anzahl verfügbarer Plätze",
        help_text="Wie viele Plätze hat der Raum?",
        min_value=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "raum_import"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Importieren"))
        self.helper.layout = Layout(
            Row(
                Column(
                    Field("url"),
                ),
            ),
            Row(
                Column(
                    Field(
                        "anzahl_plaetze",
                        css_class="col-3"
                    ),
                ),
            ),
        )

    def clean_url(self):
        url = self.cleaned_data["url"]
        param_regex = r"raum.rgid=(?P<raum_id>\d+)"

        m = re.search(param_regex, url)
        if not m:
            raise ValidationError("URL enthält keine Raum-ID (z.B. raum.rgid=2342)")
        else:
            self.raum_id = m.group("raum_id")

        if Raum.objects.filter(lsf_id=self.raum_id).exists():
            raise ValidationError("Dieser Raum existiert schon!")

        return url


class VerfuegbarkeitForm(forms.ModelForm):
    class Meta:
        model = Verfuegbarkeit
        fields = "__all__"
        widgets = {
            "datum": forms.TextInput(
                attrs={"type": "date", "value": timezone.localdate()}
            ),
            "beginn": forms.TextInput(attrs={"type": "time"}),
            "ende": forms.TextInput(attrs={"type": "time"}),
            "notiz": forms.Textarea(attrs={"rows": 1}),
        }

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_id = "verfuegbarkeit"
        helper.layout = Layout(
            Row(
                Column(
                    Field("datum"),
                    css_class="col-2",
                ),
                Column(
                    Field("beginn"),
                    css_class="col-2",
                ),
                Column(
                    Field("ende"),
                    css_class="col-2",
                ),
                Column(
                    Field("raum"),
                ),
            ),
            Row(
                Column(
                    Field("notiz"),
                ),
            ),
            Row(
                Column(
                    Submit("submit", "Hinzufügen"),
                ),
                Column(
                    HTML("""
                        {% if object %}
                        <a href="{% url 'ausleihe:verfuegbarkeit-delete' object.id %}"
                        class="btn btn-danger" role="button">Löschen</a>
                        {% endif %}
                    """
                    ),
                    css_class="col-3 text-right",
                ),
            ),
        )

        return helper


class ReservierungszeitForm(forms.Form):
    zeit = forms.TimeField(
        label="Uhrzeit",
        widget=forms.TextInput(attrs={"type": "time"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.helper = FormHelper()
        self.helper.form_id = "reservierungszeit"
        self.helper.form_method = "post"
        self.helper.form_error_title = "Konnte nicht reservieren"
        self.helper.add_input(Submit("submit", "Reservieren"))
        self.helper.layout = Layout(
            Row(
                Column(
                    HTML("""
                    <p>Für den Skill sind {{ skill.dauer }} min eingeplant.</p>
                    <p>Wähle eine Zeit zwischen
                    {{ verfuegbarkeit.beginn }} – {{ v_ende }} Uhr
                    im 15-Minuten-Takt:</p>
                    """
                    ),
                ),
            ),
            Row(
                Column(
                    Field("zeit"),
                    css_class="col-3",
                )
            )
        )

        v = kwargs.get("verfuegbarkeit", None)
        if v:
            self.verfuegbarkeit = v
            self.fields["zeit"].initial = v.beginn
            self.fields["zeit"].widget.attrs["min"] = v.beginn

        v_ende = kwargs.get("v_ende", None)
        if v_ende:
            self.v_ende = v_ende
            self.fields["zeit"].widget.attrs["max"] = v_ende

        self.fields["zeit"].widget.attrs["step"] = 15*60

    def clean_zeit(self):
        zeit = self.cleaned_data["zeit"]

        if not (self.verfuegbarkeit.beginn <= zeit <= self.v_ende):
            raise ValidationError("Zeit befindet sich nicht im gültigen Rahmen.")

        return zeit
