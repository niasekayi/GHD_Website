from django.shortcuts import render
from services.models import ServiceCategory
from pages.models import GalleryPhoto
from booking.models import BookingSettings


def pricing(request):
    categories = ServiceCategory.objects.prefetch_related('services').order_by('order', 'name')
    gallery_service_ids = set(
        GalleryPhoto.objects.filter(is_active=True, service__isnull=False)
        .values_list('service_id', flat=True)
    )
    return render(request, 'pages/pricing/pricing.html', {
        'categories': categories,
        'gallery_service_ids': gallery_service_ids,
        'deposit_amount': int(BookingSettings.get().deposit_amount),
    })
