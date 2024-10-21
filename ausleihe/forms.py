from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Submit,
    Layout,
    Div,
    Field,
    Row,
    Column,
)
from crispy_forms.bootstrap import (
    InlineCheckboxes,
)

from .models import (
    Raum,
    Skill,
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


class RaumForm(forms.ModelForm):
    class Meta:
        model = Raum
        fields = [
            "name",
            "lsf_id",
            "anzahl_plaetze",
        ]

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
