"""
Send 24-hour appointment reminder emails and SMS to clients.

Schedule this to run daily — e.g.:
  Windows Task Scheduler: run daily at 9 AM
    Action: python manage.py send_reminders

  Linux cron (crontab -e):
    0 9 * * * cd /path/to/project && venv/bin/python manage.py send_reminders
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from booking.models import Appointment
from booking.email_utils import send_reminder_email
from booking.sms_utils import send_reminder_sms


class Command(BaseCommand):
    help = 'Send reminder emails/SMS to clients with appointments tomorrow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-ahead', type=int, default=1,
            help='Send reminders for appointments this many days from now (default: 1 = tomorrow)'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Print which reminders would be sent without actually sending'
        )

    def handle(self, *args, **options):
        target = date.today() + timedelta(days=options['days_ahead'])
        appointments = Appointment.objects.filter(
            date=target,
            status__in=['pending', 'confirmed'],
            reminder_sent=False,
        ).select_related('service')

        if not appointments.exists():
            self.stdout.write(f'No appointments found for {target}.')
            return

        count = 0
        for appt in appointments:
            label = f'{appt.client_name} — {appt.service.name if appt.service else "Consultation"} at {appt.start_time.strftime("%I:%M %p").lstrip("0")} on {target}'

            if options['dry_run']:
                self.stdout.write(f'  [DRY RUN] Would remind: {label}')
            else:
                send_reminder_email(appt)
                send_reminder_sms(appt)
                appt.reminder_sent = True
                appt.save(update_fields=['reminder_sent'])
                self.stdout.write(f'  Reminded: {label}')
                count += 1

        if not options['dry_run']:
            self.stdout.write(self.style.SUCCESS(f'Reminders sent: {count}'))
        else:
            self.stdout.write(self.style.WARNING(f'Dry run complete — {appointments.count()} would be sent.'))
