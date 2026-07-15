from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/create-paypal-order/', views.api_create_paypal_order, name='api_create_paypal_order'),
    path('api/capture-order/', views.api_capture_order, name='api_capture_order'),
]
