# Generated manually for TASK-026 on 2025-12-09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_add_medication_session_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckInLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('check_in_time', models.DateTimeField()),
                ('room_condition', models.CharField(choices=[('excellent', 'Отличное'), ('good', 'Хорошее'), ('fair', 'Удовлетворительное'), ('poor', 'Требует внимания')], max_length=20)),
                ('temperature', models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True)),
                ('blood_pressure_systolic', models.IntegerField(blank=True, null=True)),
                ('blood_pressure_diastolic', models.IntegerField(blank=True, null=True)),
                ('pulse', models.IntegerField(blank=True, null=True)),
                ('weight', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('allergies', models.TextField(blank=True, null=True)),
                ('current_medications', models.TextField(blank=True, null=True)),
                ('medical_conditions', models.TextField(blank=True, null=True)),
                ('mobility_status', models.CharField(choices=[('fully_mobile', 'Полностью мобильный'), ('needs_assistance', 'Нуждается в помощи'), ('wheelchair', 'Инвалидная коляска'), ('bedridden', 'Лежачий')], db_index=True, default='fully_mobile', max_length=30)),
                ('special_dietary_requirements', models.TextField(blank=True, null=True)),
                ('emergency_contact_name', models.CharField(blank=True, max_length=255, null=True)),
                ('emergency_contact_phone', models.CharField(blank=True, max_length=50, null=True)),
                ('emergency_contact_relationship', models.CharField(blank=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('belongings_checked', models.BooleanField(default=False)),
                ('room_orientation_completed', models.BooleanField(default=False)),
                ('facility_tour_completed', models.BooleanField(default=False)),
                ('documents_signed', models.BooleanField(default=False)),
                ('booking', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='check_in_logs', to='core.booking')),
                ('booking_detail', models.OneToOneField(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='check_in_log', to='core.bookingdetail')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkinlog_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkinlog_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Check-in log',
                'verbose_name_plural': 'Check-in logs',
                'ordering': ['-check_in_time'],
            },
        ),
        migrations.AddIndex(
            model_name='checkinlog',
            index=models.Index(fields=['booking', '-check_in_time'], name='idx_checkin_booking_time'),
        ),
        migrations.AddIndex(
            model_name='checkinlog',
            index=models.Index(fields=['booking_detail'], name='idx_checkin_detail'),
        ),
        migrations.AddIndex(
            model_name='checkinlog',
            index=models.Index(fields=['mobility_status'], name='idx_checkin_mobility'),
        ),
    ]
