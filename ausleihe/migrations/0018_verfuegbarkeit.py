# Generated by Django 3.2.25 on 2024-10-23 15:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ausleihe', '0017_auto_20241022_1638'),
    ]

    operations = [
        migrations.CreateModel(
            name='Verfuegbarkeit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField()),
                ('beginn', models.TimeField()),
                ('ende', models.TimeField()),
                ('notiz', models.TextField(blank=True)),
                ('raum', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ausleihe.raum')),
            ],
            options={
                'verbose_name': 'Verfügbarkeit',
                'verbose_name_plural': 'Verfügbarkeiten',
                'ordering': ('datum', 'beginn', 'raum'),
            },
        ),
    ]