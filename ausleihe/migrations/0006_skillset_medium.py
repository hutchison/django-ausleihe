# Generated by Django 3.2.25 on 2024-05-01 12:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ausleihe', '0005_skillset_skillsetitem_skillsetitemrelation'),
    ]

    operations = [
        migrations.AddField(
            model_name='skillset',
            name='medium',
            field=models.ForeignKey(default='00000', on_delete=django.db.models.deletion.CASCADE, related_name='skillsets', to='ausleihe.medium'),
            preserve_default=False,
        ),
    ]
