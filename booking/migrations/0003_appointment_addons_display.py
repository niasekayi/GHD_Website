from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0002_appointment_reminder_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='addons_display',
            field=models.TextField(blank=True, default='', help_text='Selected add-on service names, comma-separated'),
        ),
    ]
