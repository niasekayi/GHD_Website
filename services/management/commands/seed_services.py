from django.core.management.base import BaseCommand
from services.models import ServiceCategory, Service


SEED_DATA = [
    {
        'category': 'Styling', 'order': 1,
        'services': [
            {
                'name': 'Silk Press',
                'price_display': '$100+',
                'duration': '2 hrs',
                'deposit_amount': '40.00',
                'is_addon': False,
                'description': 'Hair is cleansed and hydrated, blown out, and styled with irons for a smooth, sleek finish.',
                'order': 0,
            },
            {
                'name': 'Silk Press Plus',
                'price_display': '$150+',
                'duration': '2.5 hrs',
                'deposit_amount': '50.00',
                'is_addon': False,
                'description': 'Hair is cleansed, hydrated, and treated with a custom cocktail tailored to your needs, assisted by an ionized steamer. Blown out and styled.',
                'order': 1,
            },
            {
                'name': 'Silk Press Deluxe',
                'price_display': '$180+',
                'duration': '3 hrs',
                'deposit_amount': '60.00',
                'is_addon': False,
                'description': 'Hair is cleansed, hydrated, and treated with a custom cocktail tailored to your needs, assisted by an ionized steamer. Blown out, trimmed with precision, and styled.',
                'order': 2,
            },
            {
                'name': 'Blowout',
                'price_display': '$80+',
                'duration': '1 hr',
                'deposit_amount': '30.00',
                'is_addon': False,
                'description': 'Hair is cleansed and hydrated, thermally protected, and blown out with a dryer and styling brushes. No irons used.',
                'order': 3,
            },
            {
                'name': 'Styled Only',
                'price_display': '$40+',
                'duration': '1 hr',
                'deposit_amount': '0.00',
                'is_addon': False,
                'description': 'Hair must be cleansed prior to arrival. Styling service only — no shampoo included.',
                'order': 4,
            },
            {
                'name': 'Shampoo Set',
                'price_display': '$85+',
                'duration': '2 hrs',
                'deposit_amount': '35.00',
                'is_addon': False,
                'description': 'Hair is cleansed and hydrated, then set with rollers, placed under dryer until dry, then styled.',
                'order': 5,
            },
            {
                'name': 'Wrap and Set (Pixie Length Only)',
                'price_display': '$50+',
                'duration': '1 hr',
                'deposit_amount': '25.00',
                'is_addon': False,
                'description': 'For pixie-length hair. Hair is cleansed and hydrated. Wet set with foam, placed under the dryer, combed out, styled, and lined up.',
                'order': 6,
            },
            {
                'name': 'Wrap and Curl (Pixie Length Only)',
                'price_display': '$80+',
                'duration': '1.5 hrs',
                'deposit_amount': '30.00',
                'is_addon': False,
                'description': 'For pixie-length hair. Hair is cleansed and hydrated. Wet set with foam, placed under dryer, curled, and lined up.',
                'order': 7,
            },
        ],
    },
    {
        'category': 'Chemical Services', 'order': 2,
        'services': [
            {
                'name': 'Relaxer – Partial',
                'price_display': '$60',
                'duration': '1 hr',
                'deposit_amount': '25.00',
                'is_addon': False,
                'description': 'Partial relaxer application with a hydration cocktail to restore bonds broken down by the chemical process. Does not include styling services.',
                'order': 0,
            },
            {
                'name': 'Relaxer – Pixie',
                'price_display': '$75',
                'duration': '1 hr',
                'deposit_amount': '30.00',
                'is_addon': False,
                'description': 'Full relaxer for pixie-length hair with hydration treatment to restore bonds. Does not include styling services.',
                'order': 1,
            },
            {
                'name': 'Relaxer – Full/Virgin',
                'price_display': '$150+',
                'duration': '2 hrs',
                'deposit_amount': '50.00',
                'is_addon': False,
                'description': 'First-time or full-head relaxer application with a thorough hydration cocktail to restore bonds. Does not include styling services.',
                'order': 2,
            },
            {
                'name': 'Custom Color (Lift)',
                'price_display': '$250+',
                'duration': '3 hrs',
                'deposit_amount': '75.00',
                'is_addon': False,
                'description': 'Hair is colored lighter than your current color. Includes cleanse and hydration cocktail to restore bonds broken down by the color process. Does not include styling services.',
                'order': 3,
            },
            {
                'name': 'Custom Color (Lift) Touch Up',
                'price_display': '$125+',
                'duration': '1 hr',
                'deposit_amount': '50.00',
                'is_addon': False,
                'description': 'Touch up of an existing lighter color with an inch or less of new growth. Does not include styling services.',
                'order': 4,
            },
            {
                'name': 'Custom Color (Deposit/Darken)',
                'price_display': '$150+',
                'duration': '2 hrs',
                'deposit_amount': '50.00',
                'is_addon': False,
                'description': 'Hair is colored darker than your current color. Includes cleanse and hydration cocktail to restore bonds. Does not include styling services.',
                'order': 5,
            },
            {
                'name': 'Custom Color (Deposit) Touch Up',
                'price_display': '$100',
                'duration': '1 hr',
                'deposit_amount': '40.00',
                'is_addon': False,
                'description': 'Touch up of an existing darker color with an inch or less of new growth. Does not include styling services.',
                'order': 6,
            },
            {
                'name': 'Rinse (Temporary Dye)',
                'price_display': '$25+',
                'duration': '30 min',
                'deposit_amount': '0.00',
                'is_addon': False,
                'description': 'A mild temporary hair color, great for covering grays or adding a shiny topcoat. Does not include styling services.',
                'order': 7,
            },
            {
                'name': 'Hi-Lites',
                'price_display': '$250+',
                'duration': '3 hrs',
                'deposit_amount': '75.00',
                'is_addon': False,
                'description': 'Small sections of hair are weaved out and lightened for a multi-dimensional color effect. Includes cleanse and hydration cocktail. Does not include styling services.',
                'order': 8,
            },
        ],
    },
    {
        'category': 'Extensions', 'order': 3,
        'services': [
            {
                'name': 'Traditional Sew-In',
                'price_display': '$380+',
                'duration': '3 hrs',
                'deposit_amount': '100.00',
                'is_addon': False,
                'description': 'Hair is cleansed and hydrated, braided down in a proper pattern for an undetectable install. Net, thread, and hook needles used. Basic cut and style included. Hair not included.',
                'order': 0,
            },
            {
                'name': 'Microlinks – Full Head',
                'price_display': '$1,000',
                'duration': '3 hrs',
                'deposit_amount': '150.00',
                'is_addon': False,
                'description': 'Hair is cleansed and hydrated. Keratin-coated beaded clamps build a bridge at the base of your hair shaft; a track is then attached for a seamless install. Basic cut and style included. Hair not included.',
                'order': 1,
            },
            {
                'name': 'Microlinks – Per Row',
                'price_display': '$150 per row',
                'duration': '1 hr',
                'deposit_amount': '50.00',
                'is_addon': False,
                'description': 'Individual row microlink installation. Price is per row. Hair not included.',
                'order': 2,
            },
            {
                'name': 'Quikweave',
                'price_display': '$175+',
                'duration': '2 hrs',
                'deposit_amount': '60.00',
                'is_addon': False,
                'description': 'Hair is cleansed and hydrated, braided flat, molded with a protectant, then tracks are bonded in. Cut and styled. Uses cap, glue, and thread. Hair not included.',
                'order': 3,
            },
            {
                'name': 'Quikweave Xpress',
                'price_display': '$285',
                'duration': '2 hrs',
                'deposit_amount': '75.00',
                'is_addon': False,
                'description': '2 bags of 14"–18" beauty supply hair included. Hair is cleansed, braided flat, molded, then tracks are bonded in. Cut and styled.',
                'order': 4,
            },
            {
                'name': 'Crochet',
                'price_display': 'Starting price varies',
                'duration': '2.5 hrs',
                'deposit_amount': '75.00',
                'is_addon': False,
                'description': 'A low-manipulation protective style using the crochet method to attach extension hair to a cornrow base. Pricing varies by style — contact us for a quote.',
                'order': 5,
            },
        ],
    },
    {
        'category': 'Precision Cuts', 'order': 4,
        'services': [
            {
                'name': 'Precision Cut',
                'price_display': '$100+',
                'duration': '1 hr',
                'deposit_amount': '40.00',
                'is_addon': False,
                'description': 'Hair is cleansed and hydrated, blown out, and cut with precision to request. Other thermal styling not included.',
                'order': 0,
            },
            {
                'name': 'Trim',
                'price_display': '$45',
                'duration': '30 min',
                'deposit_amount': '0.00',
                'is_addon': False,
                'description': 'For pre-straightened hair only. Cut at 0 degrees with no elevation. No thermal services included. Can be standalone or added to an existing service.',
                'order': 1,
            },
            {
                'name': "Men's Cut",
                'price_display': '$50',
                'duration': '30 min',
                'deposit_amount': '0.00',
                'is_addon': False,
                'description': "Traditional men's haircut with scissors over comb or clippers and trimmers. Shampoo included.",
                'order': 2,
            },
            {
                'name': "Men's Grooming",
                'price_display': '$25',
                'duration': '30 min',
                'deposit_amount': '0.00',
                'is_addon': True,
                'description': 'Add-on only. Trim service for eyebrows, ears, nose, mustache, and beard. Must be added to an existing appointment.',
                'order': 3,
            },
            {
                'name': 'Trim & Treat',
                'price_display': '$75',
                'duration': '30 min',
                'deposit_amount': '0.00',
                'is_addon': True,
                'description': 'Add-on only. A customized hydration treatment assisted by the ionized steamer plus a precision trim at a discounted price. Requires a service that includes a cleanse.',
                'order': 4,
            },
        ],
    },
    {
        'category': 'Treatments', 'order': 5,
        'services': [
            {
                'name': 'Hair Mask',
                'price_display': '$15',
                'duration': '10 min',
                'deposit_amount': '0.00',
                'is_addon': True,
                'description': 'Add-on only. A quick, high-intensity hair food mask for an instant nutritional blast. Requires a service that includes a cleanse.',
                'order': 0,
            },
            {
                'name': 'Hydration Treatment – Moisture',
                'price_display': '$45',
                'duration': '15 min',
                'deposit_amount': '0.00',
                'is_addon': True,
                'description': 'Add-on only. Ionized steam treatment for dry, brittle, or tightly-coiled hair. Provides an instant moisture blast and supports length retention. Requires a service that includes a cleanse.',
                'order': 1,
            },
            {
                'name': 'Hydration Treatment – Amino Acid',
                'price_display': '$50',
                'duration': '15 min',
                'deposit_amount': '0.00',
                'is_addon': True,
                'description': 'Add-on only. Ionized steam treatment for chemically treated, weak, or frayed hair. Provides an instant surge of strength and supports length retention. Requires a service that includes a cleanse.',
                'order': 2,
            },
        ],
    },
    {
        'category': 'Maintenance', 'order': 6,
        'services': [
            {
                'name': 'Traditional Sew-In Maintenance',
                'price_display': '$150+',
                'duration': '2 hrs',
                'deposit_amount': '50.00',
                'is_addon': False,
                'description': 'For existing traditional sew-in installs. Includes cleanse, hydration, track tightening, and styling. Please be prepared to sit under the dryer. Foreign maintenance +$25.',
                'order': 0,
            },
            {
                'name': 'Quikweave Maintenance',
                'price_display': '$140+',
                'duration': '2 hrs',
                'deposit_amount': '50.00',
                'is_addon': False,
                'description': 'For existing quikweave installs. Includes cleanse, hydration, track re-laying, and styling. Please be prepared to sit under the dryer.',
                'order': 1,
            },
            {
                'name': 'Microlink Maintenance',
                'price_display': '$200+',
                'duration': '2 hrs',
                'deposit_amount': '75.00',
                'is_addon': False,
                'description': 'For existing microlink installs. Includes cleanse, hydration, track tightening, and styling. Foreign maintenance +$25.',
                'order': 2,
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with Good Hair Daye services'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing services before seeding')

    def handle(self, *args, **options):
        from services.models import ServiceCategory, Service
        if options['clear']:
            Service.objects.all().delete()
            ServiceCategory.objects.all().delete()
            self.stdout.write('Cleared existing services.')
        elif Service.objects.exists():
            self.stdout.write(self.style.WARNING('Services already exist. Run with --clear to replace them.'))
            return

        created_cats = 0
        created_svcs = 0

        for cat_data in SEED_DATA:
            cat, new = ServiceCategory.objects.get_or_create(
                name=cat_data['category'],
                defaults={'order': cat_data['order']}
            )
            if new:
                created_cats += 1

            for svc in cat_data['services']:
                _, new = Service.objects.get_or_create(
                    name=svc['name'],
                    category=cat,
                    defaults={
                        'price_display': svc['price_display'],
                        'duration': svc['duration'],
                        'deposit_amount': svc['deposit_amount'],
                        'is_addon': svc['is_addon'],
                        'description': svc['description'],
                        'order': svc['order'],
                    }
                )
                if new:
                    created_svcs += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done — {created_cats} categories, {created_svcs} services created.'
        ))
