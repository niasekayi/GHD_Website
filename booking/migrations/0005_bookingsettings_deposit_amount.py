from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0004_appointment_paypal_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookingsettings',
            name='deposit_amount',
            field=models.DecimalField(decimal_places=2, default=40.0, max_digits=8),
        ),
    ]
