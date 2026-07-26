from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0005_bookingsettings_deposit_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='source',
            field=models.CharField(
                max_length=20,
                choices=[('online', 'Online'), ('manual', 'Manual')],
                default='online',
            ),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='client_email',
            field=models.EmailField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='client_phone',
            field=models.CharField(max_length=30, blank=True, default=''),
        ),
    ]
