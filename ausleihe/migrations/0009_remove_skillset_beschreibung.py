# Generated by Django 3.2.25 on 2024-10-19 16:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ausleihe', '0008_auto_20241019_1244'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='skillset',
            name='beschreibung',
        ),
    ]