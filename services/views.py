from django.shortcuts import render
from .models import ServiceCategory, Service


def index(request):
    db_services = Service.objects.filter(is_active=True).select_related('category').order_by(
        'category__order', 'order', 'name'
    )
    categories = list(
        ServiceCategory.objects.order_by('order', 'name').values_list('name', flat=True)
    )
    services = [
        {
            'id': s.id,
            'name': s.name,
            'category': s.category.name,
            'price': s.price_display,
            'duration': s.duration,
            'description': s.description,
            'deposit': str(s.deposit_amount),
            'is_addon': s.is_addon,
        }
        for s in db_services
    ]
    return render(request, 'services/index.html', {
        'services': services,
        'categories': categories,
    })
