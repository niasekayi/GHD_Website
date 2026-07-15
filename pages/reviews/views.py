from django.shortcuts import render
from ..models import Review


def reviews_page(request):
    reviews = Review.objects.filter(is_active=True)
    return render(request, 'pages/reviews/reviews.html', {'reviews': reviews})
