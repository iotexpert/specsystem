# Generated by Django 4.0.7 on 2022-09-08 15:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('spec', '0003_userwatch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdelegate',
            name='delegate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegates_for', to=settings.AUTH_USER_MODEL),
        ),
    ]
