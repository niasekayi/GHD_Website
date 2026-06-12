from django.urls import path
from .home.views import home
from .gallery.views import gallery
from .reviews.views import reviews_page
from .terms.views import terms
from .cancellation.views import cancellation
from .pricing.views import pricing
from .privacy.views import privacy

app_name = 'pages'

urlpatterns = [
    path('', home, name='home'),
    path('pricing/', pricing, name='pricing'),
    path('terms/', terms, name='terms'),
    path('cancellation-policy/', cancellation, name='cancellation'),
    path('gallery/', gallery, name='gallery'),
    path('reviews/', reviews_page, name='reviews'),
    path('privacy/', privacy, name='privacy'),
]
