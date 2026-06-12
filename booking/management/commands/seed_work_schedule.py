from datetime import time
from django.core.management.base import BaseCommand
from booking.models import WorkSchedule


SCHEDULE = [
    # (day_of_week, start, end, is_active)
    (0, time(10, 0), time(18, 0), True),   # Monday 10am-6pm
    (1, time(10, 0), time(18, 0), True),   # Tuesday 10am-6pm
    (2, None,        None,        False),  # Wednesday closed
    (3, time(10, 0), time(18, 0), True),   # Thursday 10am-6pm
    (4, time(10, 0), time(18, 0), True),   # Friday 10am-6pm
    (5, time(12, 0), time(18, 0), True),   # Saturday 12pm-6pm
    (6, None,        None,        False),  # Sunday closed
]


class Command(BaseCommand):
    help = 'Seed the weekly work schedule (Mon/Tue/Thu/Fri 10-6, Sat 12-6)'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for day, start, end, active in SCHEDULE:
            ws, new = WorkSchedule.objects.update_or_create(
                day_of_week=day,
                defaults={'start_time': start, 'end_time': end, 'is_active': active},
            )
            if new:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f'Work schedule seeded — {created} created, {updated} updated.'
        ))
