# Generated by Django 3.2.25 on 2024-10-19 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ausleihe', '0009_remove_skillset_beschreibung'),
    ]

    operations = [
        migrations.AddField(
            model_name='skill',
            name='beschreibung',
            field=models.TextField(blank=True),
        ),
    ]
