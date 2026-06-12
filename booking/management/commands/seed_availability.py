from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Deprecated — availability is now generated dynamically from WorkSchedule. Use seed_work_schedule instead.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'seed_availability is no longer used. Availability is now dynamic.\n'
            'Run: python manage.py seed_work_schedule'
        ))
