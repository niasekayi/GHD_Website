from django.db import migrations


def delete_treatments(apps, schema_editor):
    ServiceCategory = apps.get_model('services', 'ServiceCategory')
    ServiceCategory.objects.filter(name='Treatments').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_service_is_addon'),
    ]

    operations = [
        migrations.RunPython(delete_treatments, migrations.RunPython.noop),
    ]
