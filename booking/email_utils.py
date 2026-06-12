from django.core.mail import EmailMultiAlternatives
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


def send_booking_confirmation(appointment):
    ctx = _build_context(appointment)

    # ── Client confirmation ─────────────────────────────────
    client_subject = (
        f"Your appointment at Good Hair Daye is confirmed — "
        f"{appointment.date.strftime('%A, %B %d').replace(' 0', ' ')}"
    )
    client_html = render_to_string('booking/email/confirmation_client.html', ctx)
    client_txt = render_to_string('booking/email/confirmation_client.txt', ctx)

    msg = EmailMultiAlternatives(
        subject=client_subject,
        body=client_txt,
        from_email=f'Good Hair Daye <{settings.SALON_EMAIL}>',
        to=[appointment.client_email],
    )
    msg.attach_alternative(client_html, 'text/html')
    msg.send(fail_silently=True)

    # ── Stylist notification ────────────────────────────────
    stylist_subject = (
        f"New Booking — {appointment.client_name} · "
        f"{ctx['service_name']} · "
        f"{appointment.date.strftime('%a %b %d').replace(' 0', ' ')}"
    )
    stylist_html = render_to_string('booking/email/confirmation_stylist.html', ctx)
    stylist_txt = render_to_string('booking/email/confirmation_stylist.txt', ctx)

    msg2 = EmailMultiAlternatives(
        subject=stylist_subject,
        body=stylist_txt,
        from_email=f'Good Hair Daye Booking <{settings.SALON_EMAIL}>',
        to=[settings.SALON_EMAIL],
    )
    msg2.attach_alternative(stylist_html, 'text/html')
    msg2.send(fail_silently=True)


def send_reminder_email(appointment):
    ctx = _build_context(appointment)

    subject = (
        f"Reminder: Your appointment is tomorrow — "
        f"{ctx['service_name']} at {ctx['time']}"
    )
    html = render_to_string('booking/email/reminder_client.html', ctx)
    txt = render_to_string('booking/email/reminder_client.txt', ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=txt,
        from_email=f'Good Hair Daye <{settings.SALON_EMAIL}>',
        to=[appointment.client_email],
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=True)
