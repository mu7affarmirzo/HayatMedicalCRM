# Generated by Django 5.2 on 2025-05-18 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_medicationsession_delete_medicationadministration_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='individualproceduresessionmodel',
            name='scheduled_to',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата '),
        ),
    ]
