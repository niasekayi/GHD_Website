from django.conf import settings


def _clean_phone(raw):
    digits = ''.join(c for c in raw if c.isdigit())
    if len(digits) == 10:
        digits = '1' + digits
    return f'+{digits}' if digits else None


def _get_client():
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_num = getattr(settings, 'TWILIO_FROM_NUMBER', '')
    if not all([sid, token, from_num]):
        return None, None
    try:
        from twilio.rest import Client
        return Client(sid, token), from_num
    except ImportError:
        return None, None


def send_booking_sms(appointment):
    client, from_num = _get_client()
    if not client:
        return

    phone = _clean_phone(appointment.client_phone)
    if not phone:
        return

    service_name = appointment.service.name if appointment.service else 'Consultation'
    date_str = appointment.date.strftime('%A, %B %d').replace(' 0', ' ')
    time_str = appointment.start_time.strftime('%I:%M %p').lstrip('0')
    first = appointment.client_name.split()[0]

    body = (
        f"Hi {first}! Your {service_name} at Good Hair Daye is confirmed "
        f"for {date_str} at {time_str}. "
        f"Deposit: ${appointment.total_deposit:.2f} due within 24 hrs via Venmo/CashApp/Zelle. "
        f"Questions? {settings.SALON_EMAIL}"
    )

    try:
        client.messages.create(body=body, from_=from_num, to=phone)
    except Exception:
        pass


def send_reminder_sms(appointment):
    client, from_num = _get_client()
    if not client:
        return

    phone = _clean_phone(appointment.client_phone)
    if not phone:
        return

    service_name = appointment.service.name if appointment.service else 'Consultation'
    time_str = appointment.start_time.strftime('%I:%M %p').lstrip('0')
    first = appointment.client_name.split()[0]

    body = (
        f"Hi {first}! Reminder — your {service_name} at Good Hair Daye is TOMORROW at {time_str}. "
        f"470 L'Enfant Plaza Center, Unit 429, Washington D.C. "
        f"Need to cancel? 48hr notice required. {settings.SALON_EMAIL}"
    )

    try:
        client.messages.create(body=body, from_=from_num, to=phone)
    except Exception:
        pass
