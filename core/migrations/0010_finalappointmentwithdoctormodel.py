# Generated by Django 5.2 on 2025-04-24 11:53

import core.models.base
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_consultingwithcardiologistmodel_state_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinalAppointmentWithDoctorModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('state', models.CharField(choices=[('активное', 'активное'), ('пассивное', 'пассивное'), ('вынужденное', 'вынужденное')], default='Приём завершён', max_length=250)),
                ('objective_status', models.TextField(blank=True, null=True)),
                ('file', models.FileField(blank=True, null=True, upload_to=core.models.base.upload_location)),
                ('height', models.FloatField(blank=True, null=True)),
                ('weight', models.FloatField(blank=True, null=True)),
                ('heart_beat', models.IntegerField(blank=True, null=True)),
                ('arterial_high_low', models.CharField(blank=True, max_length=255, null=True)),
                ('arterial_high', models.IntegerField(blank=True, null=True)),
                ('arterial_low', models.IntegerField(blank=True, null=True)),
                ('imt', models.FloatField(blank=True, null=True)),
                ('imt_interpretation', models.FloatField(blank=True, null=True)),
                ('summary', models.TextField(blank=True, null=True)),
                ('treatment_results', models.CharField(choices=[('Улучение', 'Улучение'), ('Без изменения', 'Без изменения'), ('Ухудшение', 'Ухудшение')], default='Улучение', max_length=250)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('diagnosis', models.ManyToManyField(to='core.diagnosistemplate')),
                ('doctor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('illness_history', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='final_appointment', to='core.illnesshistory')),
                ('modified_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
