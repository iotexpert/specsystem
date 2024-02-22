# Generated by Django 4.1.8 on 2024-02-19 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spec', '0010_spec_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='active',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='doctype',
            name='active',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='location',
            name='active',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='role',
            name='active',
            field=models.BooleanField(blank=True, default=True),
        ),
    ]
