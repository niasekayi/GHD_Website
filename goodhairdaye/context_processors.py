from django.conf import settings


def site_settings(request):
    from pages.models import BannerAlert
    try:
        active_banner = BannerAlert.objects.filter(is_active=True).first()
    except Exception:
        active_banner = None

    return {
        'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID,
        'PAYPAL_MODE': settings.PAYPAL_MODE,
        'active_banner': active_banner,
        'SITE_URL': settings.SITE_URL,
    }
