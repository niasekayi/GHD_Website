from django.shortcuts import render
from pages.models import GalleryPhoto


def gallery(request):
    photos = GalleryPhoto.objects.filter(is_active=True).select_related('service')
    return render(request, 'pages/gallery/gallery.html', {'photos': photos})
