# Generated by Django 3.2.25 on 2024-11-09 13:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ausleihe', '0022_leihe_anfang_ende'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservierung',
            name='leihe',
            field=models.OneToOneField(blank=True, help_text='Wenn eine Reservierung wirklich ausgeliehen wurde, wird hier die Leihe verlinkt.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='reservierung', to='ausleihe.leihe'),
        ),
    ]