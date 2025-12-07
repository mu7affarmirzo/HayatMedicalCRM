# Generated manually on 2025-12-07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_add_medication_unit_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicationsession',
            name='quantity',
            field=models.PositiveIntegerField(
                default=1,
                help_text="Number of units dispensed in this session"
            ),
        ),
    ]
