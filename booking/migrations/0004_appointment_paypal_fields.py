from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0003_appointment_addons_display'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='paypal_order_id',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('paid', 'Paid'), ('refunded', 'Refunded')],
                default='pending',
                max_length=20,
            ),
        ),
    ]
