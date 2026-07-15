from django.conf import settings
from django.shortcuts import render
from django.core.mail import send_mail
from ..data import BRANDS
from ..models import Review
from .forms import CommunityForm


def home(request):
    form = CommunityForm()
    success = False

    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            first = form.cleaned_data['first_name']
            last  = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            try:
                send_mail(
                    subject=f'New Community Sign-Up: {first} {last}',
                    message=f'Name: {first} {last}\nEmail: {email}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.SALON_EMAIL],
                    fail_silently=True,
                )
            except Exception:
                pass
            form = CommunityForm()
            success = True

    reviews = Review.objects.filter(is_active=True)[:3]
    return render(request, 'pages/home/home.html', {
        'brands': BRANDS,
        'reviews': reviews,
        'form': form,
        'success': success,
    })
