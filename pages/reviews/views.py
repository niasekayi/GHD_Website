from django.shortcuts import render
from ..data import REVIEWS


def reviews_page(request):
    return render(request, 'pages/reviews/reviews.html', {'reviews': REVIEWS})
