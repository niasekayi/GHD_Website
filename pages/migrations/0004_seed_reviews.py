from django.db import migrations


def seed_reviews(apps, schema_editor):
    Review = apps.get_model('pages', 'Review')
    reviews = [
        {
            'client_name': 'Adrianne Boyd',
            'rating': 5,
            'body': "Shout out to Dommi Good for doing my mom’s hair.. It looks amazing.. She loves it!!! I highly recommend her if anyone is looking to get their hair done!",
            'order': 1,
            'is_active': True,
        },
        {
            'client_name': 'Evangeline Prince',
            'rating': 5,
            'body': "I had a wonderful time with Dommi. She is the first person in 9 years to touch my hair.",
            'order': 2,
            'is_active': True,
        },
        {
            'client_name': 'Tashea Evette',
            'rating': 5,
            'body': "I cried to have my blonde back & I’m so happy with the outcome. If you need some color, go to see my girl Dommi Good, she is a beast with it!",
            'order': 3,
            'is_active': True,
        },
    ]
    for r in reviews:
        Review.objects.get_or_create(client_name=r['client_name'], defaults=r)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0003_galleryphoto_service'),
    ]

    operations = [
        migrations.RunPython(seed_reviews, migrations.RunPython.noop),
    ]
