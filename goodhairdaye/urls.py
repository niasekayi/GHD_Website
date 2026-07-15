from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import HttpResponse


def sitemap_view(request):
    content = render(request, 'sitemap.xml', {'SITE_URL': settings.SITE_URL})
    return HttpResponse(content.content, content_type='application/xml')


def robots_view(request):
    content = render(request, 'robots.txt', {'SITE_URL': settings.SITE_URL})
    return HttpResponse(content.content, content_type='text/plain')


urlpatterns = [
    path('sitemap.xml', sitemap_view),
    path('robots.txt',  robots_view),
    path('admin/', include('goodhairdaye.admin_urls')),
    path('', include('pages.urls')),
    path('book/', include('booking.urls')),
    path('shop/', include('shop.urls')),
    path('services/', include('services.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
