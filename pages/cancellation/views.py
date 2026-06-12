from django.shortcuts import render


def cancellation(request):
    return render(request, 'pages/cancellation/cancellation.html')
