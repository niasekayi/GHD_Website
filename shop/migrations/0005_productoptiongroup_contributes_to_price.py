from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_productvariant'),
    ]

    operations = [
        migrations.AddField(
            model_name='productoptiongroup',
            name='contributes_to_price',
            field=models.BooleanField(
                default=False,
                help_text='Check this if selecting a value in this group changes the price (e.g. Hair Length). Leave unchecked for purely descriptive options like Hair Texture.',
            ),
        ),
    ]
