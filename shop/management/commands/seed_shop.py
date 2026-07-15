from django.core.management.base import BaseCommand
from shop.models import ProductCategory, Product


SEED_DATA = [
    {
        'category': 'Products', 'order': 1,
        'products': [
            {'name': 'Bundle 1', 'price': '25.00', 'stock_quantity': 10, 'description': 'Placeholder', 'order': 0},
            {'name': 'Bundle 2', 'price': '25.00', 'stock_quantity': 10, 'description': 'Placeholder', 'order': 1},
            {'name': 'Bundle 3', 'price': '25.00', 'stock_quantity': 10, 'description': 'Placeholder', 'order': 2},
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with placeholder Good Hair Daye shop products'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing products before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            Product.objects.all().delete()
            ProductCategory.objects.all().delete()
            self.stdout.write('Cleared existing shop products.')
        elif Product.objects.exists():
            self.stdout.write(self.style.WARNING('Products already exist. Run with --clear to replace them.'))
            return

        created_cats = 0
        created_products = 0

        for cat_data in SEED_DATA:
            cat, new = ProductCategory.objects.get_or_create(
                name=cat_data['category'],
                defaults={'order': cat_data['order']}
            )
            if new:
                created_cats += 1

            for product in cat_data['products']:
                _, new = Product.objects.get_or_create(
                    name=product['name'],
                    category=cat,
                    defaults={
                        'price': product['price'],
                        'stock_quantity': product['stock_quantity'],
                        'description': product['description'],
                        'order': product['order'],
                    }
                )
                if new:
                    created_products += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done — {created_cats} categories, {created_products} products created.'
        ))
