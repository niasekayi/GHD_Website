from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='BannerAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(help_text='Text shown in the banner across the top of every page.', max_length=300)),
                ('link_text', models.CharField(blank=True, help_text='Optional button text, e.g. "Book Now"', max_length=100)),
                ('link_url', models.CharField(blank=True, help_text='Optional URL the button links to', max_length=200)),
                ('style', models.CharField(choices=[('promo', 'Promo — Gold'), ('info', 'Info — Tan'), ('deal', 'Deal — Green')], default='promo', max_length=20)),
                ('is_active', models.BooleanField(default=True, help_text='Check to show this banner on the site right now.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Banner / Announcement',
                'verbose_name_plural': 'Banners & Announcements',
                'ordering': ['-created_at'],
            },
        ),
    ]
