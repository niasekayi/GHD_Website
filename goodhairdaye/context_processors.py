from django.conf import settings


def site_settings(request):
    from pages.models import BannerAlert
    try:
        active_banner = BannerAlert.objects.filter(is_active=True).first()
    except Exception:
        active_banner = None

    return {
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
        'active_banner': active_banner,
        'SITE_URL': settings.SITE_URL,
    }
