import resend
from django.template.loader import render_to_string
from django.conf import settings


def _build_context(appointment):
    service_name = appointment.service.name if appointment.service else 'Consultation'
    date_str = appointment.date.strftime('%A, %B %d, %Y').replace(' 0', ' ')
    time_str = appointment.start_time.strftime('%I:%M %p').lstrip('0')
    return {
        'appointment': appointment,
        'first_name': appointment.client_name.split()[0],
        'service_name': service_name,
        'date': date_str,
        'time': time_str,
        'total_deposit': f'{appointment.total_deposit:.2f}',
        'salon_email': settings.SALON_EMAIL,
    }


RESEND_FROM = 'Good Hair Daye <info@goodhairdaye.com>'


def _send(*, to, subject, html, text):
    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send({
        'from': RESEND_FROM,
        'to': to if isinstance(to, list) else [to],
        'subject': subject,
        'html': html,
        'text': text,
    })


def send_booking_confirmation(appointment):
    ctx = _build_context(appointment)

    client_subject = (
        f"Your appointment at Good Hair Daye is confirmed — "
        f"{appointment.date.strftime('%A, %B %d').replace(' 0', ' ')}"
    )
    _send(
        to=appointment.client_email,
        subject=client_subject,
        html=render_to_string('booking/email/confirmation_client.html', ctx),
        text=render_to_string('booking/email/confirmation_client.txt', ctx),
    )

    stylist_subject = (
        f"New Booking — {appointment.client_name} · "
        f"{ctx['service_name']} · "
        f"{appointment.date.strftime('%a %b %d').replace(' 0', ' ')}"
    )
    stylist_recipients = list({settings.SALON_EMAIL, 'info@goodhairdaye.com'})
    _send(
        to=stylist_recipients,
        subject=stylist_subject,
        html=render_to_string('booking/email/confirmation_stylist.html', ctx),
        text=render_to_string('booking/email/confirmation_stylist.txt', ctx),
    )


def send_reminder_email(appointment):
    ctx = _build_context(appointment)
    subject = (
        f"Reminder: Your appointment is tomorrow — "
        f"{ctx['service_name']} at {ctx['time']}"
    )
    _send(
        to=appointment.client_email,
        subject=subject,
        html=render_to_string('booking/email/reminder_client.html', ctx),
        text=render_to_string('booking/email/reminder_client.txt', ctx),
    )
