# Generated by Django 3.2.25 on 2024-10-19 17:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ausleihe', '0010_skill_beschreibung'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skillset',
            name='skill',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='skillsets', to='ausleihe.skill'),
        ),
    ]