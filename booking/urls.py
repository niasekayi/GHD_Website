from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/services/', views.api_services, name='api_services'),
    path('api/availability/', views.api_availability, name='api_availability'),
    path('api/create-payment-intent/', views.api_create_payment_intent, name='api_create_payment_intent'),
    path('api/book/', views.api_book, name='api_book'),
]
