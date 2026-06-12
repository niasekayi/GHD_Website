from django.shortcuts import render


def pricing(request):
    return render(request, 'pages/pricing/pricing.html')
