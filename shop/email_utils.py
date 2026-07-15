from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def _build_context(order):
    return {
        'order': order,
        'first_name': order.customer_name.split()[0],
        'items': list(order.items.all()),
        'salon_email': settings.SALON_EMAIL,
    }


def send_order_emails(order):
    ctx = _build_context(order)

    # ── Customer confirmation ───────────────────────────────
    client_subject = f'Your Good Hair Daye order {order.order_number} is confirmed'
    client_html = render_to_string('shop/email/order_confirmation_client.html', ctx)
    client_txt = render_to_string('shop/email/order_confirmation_client.txt', ctx)

    msg = EmailMultiAlternatives(
        subject=client_subject,
        body=client_txt,
        from_email=f'Good Hair Daye <{settings.SALON_EMAIL}>',
        to=[order.customer_email],
    )
    msg.attach_alternative(client_html, 'text/html')
    msg.send(fail_silently=True)

    # ── Owner notification ──────────────────────────────────
    owner_subject = f'New Shop Order — {order.order_number} · {order.customer_name}'
    owner_html = render_to_string('shop/email/order_notification_owner.html', ctx)
    owner_txt = render_to_string('shop/email/order_notification_owner.txt', ctx)

    msg2 = EmailMultiAlternatives(
        subject=owner_subject,
        body=owner_txt,
        from_email=f'Good Hair Daye Shop <{settings.SALON_EMAIL}>',
        to=[settings.SALON_EMAIL],
    )
    msg2.attach_alternative(owner_html, 'text/html')
    msg2.send(fail_silently=True)


def send_status_update_email(order):
    ctx = _build_context(order)
    subject = f'Your Good Hair Daye order {order.order_number} is now {order.get_status_display()}'
    html = render_to_string('shop/email/order_status_update.html', ctx)
    txt = render_to_string('shop/email/order_status_update.txt', ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=txt,
        from_email=f'Good Hair Daye <{settings.SALON_EMAIL}>',
        to=[order.customer_email],
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=True)
