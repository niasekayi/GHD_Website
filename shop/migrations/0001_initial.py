from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ShopItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, help_text='Display price in dollars', max_digits=8)),
                ('image', models.ImageField(blank=True, help_text='Product photo (JPG or PNG)', null=True, upload_to='shop/')),
                ('affiliate_url', models.URLField(blank=True, help_text='Link to purchase (Amazon, Amika site, etc.)')),
                ('category', models.CharField(blank=True, help_text='e.g. Hair Care, Tools, Extensions', max_length=100)),
                ('is_active', models.BooleanField(default=True, help_text='Show this item in the shop')),
                ('is_featured', models.BooleanField(default=False, help_text='Highlight this item at the top')),
                ('order', models.PositiveIntegerField(default=0, help_text='Lower number = shows first')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Shop Item',
                'verbose_name_plural': 'Shop Items',
                'ordering': ['order', 'name'],
            },
        ),
    ]
