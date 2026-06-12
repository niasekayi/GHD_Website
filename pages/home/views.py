from django.shortcuts import render
from django.core.mail import send_mail
from ..data import BRANDS, REVIEWS
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
                    from_email='noreply@goodhairdaye.com',
                    recipient_list=['info@goodhairdaye.com'],
                    fail_silently=True,
                )
            except Exception:
                pass
            form = CommunityForm()
            success = True

    return render(request, 'pages/home/home.html', {
        'brands': BRANDS,
        'reviews': REVIEWS,
        'form': form,
        'success': success,
    })
